package au.edu.monash.citizenflood.ar

import android.opengl.GLES11Ext
import android.opengl.GLES20 as GL
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import com.google.ar.core.*
import com.google.ar.core.exceptions.NotYetAvailableException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.util.concurrent.atomic.AtomicReference
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10

/** GL-thread-owned anchors and textures. Camera and depth images never leave the device. */
class DepthRenderer(
    private val depthM: Float,
    private val status: (String) -> Unit,
    private val candidateChanged: (Boolean) -> Unit,
    private val failed: () -> Unit,
    private val standalone: Boolean = false,
) : GLSurfaceView.Renderer {
    @Volatile var session: Session? = null
    @Volatile var rotation: Int = 0
    private val orbit = if (standalone) PreviewOrbit(depthM) else null
    private val patchSize = orbit?.surfaceSize ?: 3f
    private val halfExtent = patchSize / 2f
    private val floorQuad = floats(-halfExtent, 0f, -halfExtent, halfExtent, 0f, -halfExtent,
        -halfExtent, 0f, halfExtent, halfExtent, 0f, halfExtent)
    private var gpuWater: GpuWater? = null
    private val gpuClock = GpuWaveClock()
    private val lightCorrection = floatArrayOf(1f,1f,1f,1f)
    private var paused = false
    fun rotate(horizontal: Float, vertical: Float) { orbit?.rotate(horizontal, vertical) }
    fun zoom(scale: Float) { orbit?.zoom(scale) }
    fun setPaused(value: Boolean) { paused = value; rippleTimestamp = 0L; gpuClock.pause() }
    fun addRipple() { if(!gpuAction{it.disturb(0f,0f,.35f,.02f)})ripples.drop(0f, 0f, .35f, .02f) }
    fun resetScene() { reset(); orbit?.reset(); paused = false }
    private var width = 1
    private var height = 1
    private val pendingTap = AtomicReference<Pair<Float, Float>?>(null)
    private var anchor: Anchor? = null
    private var confirmed = false
    private var cameraTexture = 0
    private var depthTexture = 0
    private var cameraProgram = 0
    private var waterProgram = 0
    private var meshVbo=0
    private var gpuMeshUploaded=false
    private val attributeVbos=HashMap<String,Int>()
    private var textureSession: Session? = null
    private val corners = floats(-1f, -1f, 1f, -1f, -1f, 1f, 1f, 1f)
    private val cameraUv = floats(0f, 0f, 1f, 0f, 0f, 1f, 1f, 1f)
    private val imageUv = floats(0f, 0f, 1f, 0f, 0f, 1f, 1f, 1f)
    private val quad = floats(-1.5f, 0f, -1.5f, 1.5f, 0f, -1.5f,
        -1.5f, 0f, 1.5f, 1.5f, 0f, 1.5f)
    private val view = FloatArray(16)
    private val projection = FloatArray(16)
    private val model = FloatArray(16)
    private val mv = FloatArray(16)
    private val mvp = FloatArray(16)
    private var depthBytes: ByteBuffer? = null
    private var frameDepthAvailable = false
    private val ripples = RippleSurface()
    private val waterMesh = ByteBuffer.allocateDirect((ripples.size-1)*(ripples.size-1)*6*6*4)
        .order(ByteOrder.nativeOrder()).asFloatBuffer()
    private val cpuVertices = (ripples.size-1)*(ripples.size-1)*6
    private val gpuVertices = 96*96*6
    private val gpuMesh by lazy {
        val mesh=ByteBuffer.allocateDirect(gpuVertices*24).order(ByteOrder.nativeOrder()).asFloatBuffer()
        fun vertex(i:Int,j:Int){mesh.put(-halfExtent+i*patchSize/96);mesh.put(0f);mesh.put(-halfExtent+j*patchSize/96);mesh.put(0f);mesh.put(1f);mesh.put(0f)}
        for(j in 0 until 96)for(i in 0 until 96){vertex(i,j);vertex(i+1,j);vertex(i,j+1);vertex(i+1,j);vertex(i+1,j+1);vertex(i,j+1)}
        mesh.position(0);mesh
    }
    private var rippleTimestamp = 0L
    private var rippleClock = 0f
    private var dropClock = 0f
    private val inverseModel = FloatArray(16)
    private val localEye = FloatArray(4)
    private val worldEye = FloatArray(4)

    private fun animateWater(timestamp: Long) {
        val elapsed = if (rippleTimestamp == 0L) 0f else
            ((timestamp-rippleTimestamp)/1_000_000_000f).coerceIn(0f,.1f)
        rippleTimestamp=timestamp; rippleClock+=elapsed; dropClock+=elapsed
        if(gpuAction { gpu ->
            if(paused)gpuClock.pause()
            if(dropClock>.8f&&!paused){dropClock=0f;gpu.disturb(kotlin.math.sin(rippleClock*.71f),kotlin.math.cos(rippleClock*.53f),.22f,.006f)}
            gpu.step(if(paused)0 else gpuClock.tick(timestamp))
        })return
        if (dropClock>.8f&&!paused) {
            dropClock=0f
            ripples.drop(kotlin.math.sin(rippleClock*.71f),kotlin.math.cos(rippleClock*.53f),.22f,.006f)
        }
        repeat(if(paused){gpuClock.pause();0}else gpuClock.tick(timestamp,60)){ripples.step()}
        waterMesh.clear()
        val spacing=patchSize/(ripples.size-1)
        // Do not let decorative ripples cross the reference on very shallow reports.
        val amplitude=minOf(1f,depthM/.1f)
        fun vertex(i:Int,j:Int) {
            waterMesh.put(-halfExtent+i*spacing);waterMesh.put(ripples.height(i,j)*amplitude);waterMesh.put(-halfExtent+j*spacing)
            waterMesh.put((ripples.height(i-1,j)-ripples.height(i+1,j))*amplitude/(2f*spacing))
            waterMesh.put(1f)
            waterMesh.put((ripples.height(i,j-1)-ripples.height(i,j+1))*amplitude/(2f*spacing))
        }
        for(j in 0 until ripples.size-1) for(i in 0 until ripples.size-1) {
            vertex(i,j);vertex(i+1,j);vertex(i,j+1)
            vertex(i+1,j);vertex(i+1,j+1);vertex(i,j+1)
        }
        waterMesh.flip()
    }

    private fun gpuAction(action:(GpuWater)->Unit):Boolean {
        val gpu=gpuWater?:return false
        return try{action(gpu);true}catch(error:Exception){
            gpuWater=null;gpuClock.pause();ripples.clear();gpu.close()
            android.util.Log.w("NativeGpuWater","Runtime CPU fallback",error);false
        }
    }

    fun tap(x: Float, y: Float) { pendingTap.set(x to y) }
    fun confirmReference() {
        if (anchor?.trackingState == TrackingState.TRACKING) {
            confirmed = true; candidateChanged(false)
        }
    }
    fun reset() {
        anchor?.detach(); anchor = null; confirmed = false
        pendingTap.set(null); candidateChanged(false)
        gpuAction{it.clear()};gpuClock.pause()
        ripples.clear(); rippleTimestamp=0L; rippleClock=0f; dropClock=0f
    }

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        try {
            gpuClock.pause();rippleTimestamp=0L;dropClock=0f;rippleClock=0f;ripples.clear()
            GL.glClearColor(0f, 0f, 0f, 1f)
            if (!standalone) cameraTexture = texture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES)
            depthTexture = texture(GL.GL_TEXTURE_2D)
            GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA,1,1,0,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,ByteBuffer.allocateDirect(4))
            attributeVbos.clear();gpuMeshUploaded=false
            val ids=IntArray(1);GL.glGenBuffers(1,ids,0);meshVbo=ids[0]
            textureSession = null
            if (!standalone) cameraProgram = program(CAMERA_VERTEX, CAMERA_FRAGMENT)
            val fragment = if (standalone) WATER_FRAGMENT
                .replace("#extension GL_OES_EGL_image_external : require", "")
                .replace("uniform samplerExternalOES cameraFeed;", "")
                .replace("texture2D(cameraFeed,cameraUv).rgb", "vec3(0.0)") else WATER_FRAGMENT
            gpuWater = GpuWater.create(patchSize,minOf(.025f,depthM*.25f))
            waterProgram = try { program(if(gpuWater!=null)GPU_WATER_VERTEX else WATER_VERTEX, fragment) }
                catch(error:Exception){
                    gpuWater?.close();gpuWater=null
                    android.util.Log.w("NativeGpuWater","Surface shader compatibility fallback",error)
                    program(WATER_VERTEX,fragment)
                }
        } catch (_: Exception) { failed() }
    }
    override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) {
        width = w; height = h; GL.glViewport(0, 0, w, h)
    }
    override fun onDrawFrame(gl: GL10?) {
        GL.glClear(GL.GL_COLOR_BUFFER_BIT or GL.GL_DEPTH_BUFFER_BIT)
        if (standalone) {
            try { drawStandalone() } catch (error: Exception) {
                android.util.Log.e("WaterPreview", "3D rendering failed", error); failed()
            }
            return
        }
        val current = session ?: return
        try {
            if (textureSession !== current) {
                current.setCameraTextureName(cameraTexture); textureSession = current
            }
            current.setDisplayGeometry(rotation, width, height)
            val frame = current.update()
            if (frame.timestamp == 0L) return
            frame.transformCoordinates2d(Coordinates2d.OPENGL_NORMALIZED_DEVICE_COORDINATES,
                corners, Coordinates2d.TEXTURE_NORMALIZED, cameraUv)
            frame.transformCoordinates2d(Coordinates2d.OPENGL_NORMALIZED_DEVICE_COORDINATES,
                corners, Coordinates2d.IMAGE_NORMALIZED, imageUv)
            drawCamera()
            val camera = frame.camera
            if (camera.trackingState != TrackingState.TRACKING) {
                pendingTap.set(null); candidateChanged(false);gpuClock.pause();rippleTimestamp=0L
                status("Tracking paused. Move slowly towards a well-lit, textured surface.")
                return // Never retain virtual water when tracking is uncertain.
            }
            val tap = pendingTap.getAndSet(null)
            if (tap != null && !confirmed) {
                val hit = frame.hitTest(tap.first, tap.second).firstOrNull {
                    val plane = it.trackable as? Plane
                    plane != null && plane.type == Plane.Type.HORIZONTAL_UPWARD_FACING &&
                        plane.trackingState == TrackingState.TRACKING && plane.isPoseInPolygon(it.hitPose)
                }
                if (hit != null) {
                    anchor?.detach(); anchor = hit.createAnchor(); candidateChanged(true)
                } else status("No reference found there. Scan a visible horizontal surface and try again.")
            }
            val placed = anchor
            if (placed == null) {
                status("Move the phone slowly to scan a safe, visible surface. Tap it to select.")
                return
            }
            if (placed.trackingState != TrackingState.TRACKING) {
                candidateChanged(false);gpuClock.pause();rippleTimestamp=0L
                status("Reference tracking lost. Move slowly or reset the reference."); return
            }
            lightCorrection.fill(1f)
            if(frame.lightEstimate.state==LightEstimate.State.VALID)frame.lightEstimate.getColorCorrection(lightCorrection,0)
            camera.getViewMatrix(view, 0)
            camera.getProjectionMatrix(projection, 0, 0.05f, 100f)
            placed.pose.toMatrix(model, 0)
            val pose = frame.camera.pose
            worldEye[0] = pose.tx(); worldEye[1] = pose.ty(); worldEye[2] = pose.tz(); worldEye[3] = 1f
            if (!confirmed) {
                candidateChanged(true)
                drawWater(false, true)
                status("Reference selected: outlined 3 m patch. Confirm it matches your described surface.")
                return
            }
            animateWater(frame.timestamp)
            updateDepth(frame)
            drawWater(frameDepthAvailable, false)
            status(if (frameDepthAvailable)
                "Local illustration · depth occlusion active. Reset if the reference drifts."
                else "Simplified preview · real objects may overlap virtual water.")
        } catch (_: Exception) { failed() }
    }

    private fun drawStandalone() {
        GL.glClearColor(.035f, .065f, .06f, 1f)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT or GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_DEPTH_TEST)
        val eye = orbit!!.eye()
        worldEye[0] = eye[0]; worldEye[1] = eye[1]; worldEye[2] = eye[2]; worldEye[3] = 1f
        Matrix.setLookAtM(view, 0, eye[0], eye[1], eye[2], 0f, depthM / 2f, 0f, 0f, 1f, 0f)
        val aspect = width.toFloat() / height.coerceAtLeast(1)
        val fov = Math.toDegrees(2 * kotlin.math.atan(kotlin.math.tan(Math.toRadians(25.0)) / minOf(1f, aspect))).toFloat()
        Matrix.perspectiveM(projection, 0, fov, aspect, .05f, 10000f)
        val now = System.nanoTime()
        if (paused) rippleTimestamp = now
        animateWater(now)
        Matrix.setIdentityM(model, 0)
        drawWater(false, true, floor = true)
        Matrix.setIdentityM(model, 0)
        drawWater(false, false)
        // Make runtime shader/driver faults visible to the Activity, not a silent blank view.
        check(GL.glGetError() == GL.GL_NO_ERROR) { "Water preview GL error" }
    }

    private fun drawCamera() {
        GL.glDisable(GL.GL_DEPTH_TEST); GL.glDisable(GL.GL_BLEND)
        GL.glUseProgram(cameraProgram)
        attribute(cameraProgram, "position", corners, 2)
        attribute(cameraProgram, "uv", cameraUv, 2)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, cameraTexture)
        GL.glUniform1i(GL.glGetUniformLocation(cameraProgram, "camera"), 0)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
        disableAttributes(cameraProgram, "position", "uv")
    }

    private fun updateDepth(frame: Frame) {
        frameDepthAvailable = false
        if (session?.config?.depthMode != Config.DepthMode.AUTOMATIC) return
        try {
            frame.acquireDepthImage16Bits().use { image ->
                val plane = image.planes[0]
                val source = plane.buffer
                val size = image.width * image.height * 4
                var packed = depthBytes
                if (packed == null || packed.capacity() != size) {
                    packed = ByteBuffer.allocateDirect(size); depthBytes = packed
                }
                DepthRgbaPacking.copy(source,image.width,image.height,plane.rowStride,plane.pixelStride,packed)
                GL.glActiveTexture(GL.GL_TEXTURE1)
                GL.glBindTexture(GL.GL_TEXTURE_2D, depthTexture)
                GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA,
                    image.width, image.height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, packed)
                frameDepthAvailable = true
            }
        } catch (_: NotYetAvailableException) { /* No stale depth from an earlier frame. */ }
        catch (_: java.lang.IllegalStateException) { /* Depth unsupported. */ }
    }

    private fun drawWater(occlude: Boolean, referenceOnly: Boolean, floor: Boolean = false) {
        if(!referenceOnly&&depthM==0f){if(!standalone)drawWater(false,true);return}
        GL.glUseProgram(waterProgram)
        GL.glUniform1f(location("gpuWater"),if(gpuWater!=null)1f else 0f)
        GL.glUniform1f(location("patchSize"),patchSize)
        GL.glUniform4fv(location("lightCorrection"),1,lightCorrection,0)
        GL.glActiveTexture(GL.GL_TEXTURE2);GL.glBindTexture(GL.GL_TEXTURE_2D,gpuWater?.texture?:depthTexture)
        GL.glUniform1i(location("waterField"),2)
        GL.glEnable(GL.GL_BLEND); GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        // A selected reference is drawn at ground height; confirmed water uses reported depth.
        if (!referenceOnly) Matrix.translateM(model, 0, 0f, depthM, 0f)
        Matrix.multiplyMM(mv, 0, view, 0, model, 0)
        Matrix.multiplyMM(mvp, 0, projection, 0, mv, 0)
        uniformMatrix("mvp", mvp); uniformMatrix("mv", mv)
        Matrix.invertM(inverseModel,0,model,0)
        Matrix.multiplyMV(localEye,0,inverseModel,0,worldEye,0)
        GL.glUniform3f(location("eyeLocal"),localEye[0],localEye[1],localEye[2])
        if (!standalone) {
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,cameraTexture)
            GL.glUniform1i(location("cameraFeed"),0)
        }
        GL.glUniform1f(location("standalone"), if (standalone) 1f else 0f)
        GL.glUniform1f(location("reportedDepth"), depthM)
        GL.glUniform1f(location("halfExtent"), halfExtent)
        val camUv=FloatArray(8);cameraUv.position(0);cameraUv.get(camUv);cameraUv.position(0)
        GL.glUniform2f(location("cameraOrigin"),camUv[0],camUv[1])
        GL.glUniform2f(location("cameraX"),camUv[2]-camUv[0],camUv[3]-camUv[1])
        GL.glUniform2f(location("cameraY"),camUv[4]-camUv[0],camUv[5]-camUv[1])
        GL.glUniform1f(location("referenceOnly"), if (floor) 3f else if (referenceOnly) 1f else 0f)
        GL.glUniform1f(location("occlusion"), if (occlude) 1f else 0f)
        GL.glUniform2f(location("viewport"), width.toFloat(), height.toFloat())
        // ARCore's mapping is affine for this un-stabilised camera image.
        val u = FloatArray(8); imageUv.position(0); imageUv.get(u); imageUv.position(0)
        GL.glUniform2f(location("uvOrigin"), u[0], u[1])
        GL.glUniform2f(location("uvX"), u[2] - u[0], u[3] - u[1])
        GL.glUniform2f(location("uvY"), u[4] - u[0], u[5] - u[1])
        GL.glActiveTexture(GL.GL_TEXTURE1); GL.glBindTexture(GL.GL_TEXTURE_2D, depthTexture)
        GL.glUniform1i(location("depthImage"), 1)
        val normalLocation=GL.glGetAttribLocation(waterProgram,"surfaceNormal")
        if(referenceOnly) {
            GL.glDisableVertexAttribArray(normalLocation);GL.glVertexAttrib3f(normalLocation,0f,1f,0f)
            attribute(waterProgram,"position",if (floor) floorQuad else quad,3)
            GL.glDrawArrays(GL.GL_TRIANGLE_STRIP,0,4)
        } else {
            val positionLocation=GL.glGetAttribLocation(waterProgram,"position")
            val mesh=if(gpuWater!=null)gpuMesh else waterMesh
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER,meshVbo)
            if(gpuWater==null||!gpuMeshUploaded){
                mesh.position(0);GL.glBufferData(GL.GL_ARRAY_BUFFER,mesh.capacity()*4,mesh,if(gpuWater!=null)GL.GL_STATIC_DRAW else GL.GL_DYNAMIC_DRAW)
                gpuMeshUploaded=gpuWater!=null
            }
            GL.glEnableVertexAttribArray(positionLocation)
            GL.glVertexAttribPointer(positionLocation,3,GL.GL_FLOAT,false,24,0)
            GL.glEnableVertexAttribArray(normalLocation)
            GL.glVertexAttribPointer(normalLocation,3,GL.GL_FLOAT,false,24,12)
            GL.glDrawArrays(GL.GL_TRIANGLES,0,if(gpuWater!=null)gpuVertices else cpuVertices)
            GL.glDisableVertexAttribArray(normalLocation);GL.glVertexAttrib3f(normalLocation,0f,1f,0f)
        }
        disableAttributes(waterProgram, "position")
        if (!referenceOnly) drawRuler()
        GL.glDisable(GL.GL_BLEND)
    }

    private fun drawRuler() {
        // A vertical scale beside the bounded patch; ticks every 10 cm, up to 100 ticks.
        val verts = ArrayList<Float>()
        fun point(x: Float, y: Float) {
            verts.add(x + if (standalone) halfExtent + patchSize * .05f else 0f)
            verts.add(y); verts.add(0f)
        }
        point(0f, -depthM); point(0f, 0f)
        val count = minOf((depthM / 0.1f).toInt(), 100)
        for (i in 0..count) {
            val y = -depthM + i * 0.1f
            point(-0.035f, y); point(0.035f, y)
        }
        if (standalone) GL.glDisable(GL.GL_DEPTH_TEST) // Intentional scale overlay, never hidden by water.
        GL.glUniform1f(location("referenceOnly"), 2f)
        attribute(waterProgram, "position", floats(*verts.toFloatArray()), 3)
        GL.glLineWidth(2f)
        GL.glDrawArrays(GL.GL_LINES, 0, verts.size / 3)
        if (standalone) GL.glEnable(GL.GL_DEPTH_TEST)
        disableAttributes(waterProgram, "position")
    }
    private fun location(name: String) = GL.glGetUniformLocation(waterProgram, name)
    private fun uniformMatrix(name: String, matrix: FloatArray) =
        GL.glUniformMatrix4fv(location(name), 1, false, matrix, 0)
    private fun attribute(program: Int, name: String, data: FloatBuffer, size: Int) {
        val loc = GL.glGetAttribLocation(program, name)
        val key="$program:$name"
        val vbo=attributeVbos.getOrPut(key){val ids=IntArray(1);GL.glGenBuffers(1,ids,0);ids[0]}
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER,vbo);data.position(0)
        GL.glBufferData(GL.GL_ARRAY_BUFFER,data.capacity()*4,data,GL.GL_DYNAMIC_DRAW)
        GL.glEnableVertexAttribArray(loc)
        GL.glVertexAttribPointer(loc, size, GL.GL_FLOAT, false, 0, 0)
    }
    private fun disableAttributes(program: Int, vararg names: String) {
        for (name in names) GL.glDisableVertexAttribArray(GL.glGetAttribLocation(program, name))
    }
    private fun texture(target: Int): Int {
        val id = IntArray(1); GL.glGenTextures(1, id, 0); GL.glBindTexture(target, id[0])
        GL.glTexParameteri(target, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(target, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(target, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(target, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        return id[0]
    }
    private fun program(vertex: String, fragment: String): Int {
        fun shader(type: Int, source: String): Int {
            val shader = GL.glCreateShader(type); GL.glShaderSource(shader, source); GL.glCompileShader(shader)
            val ok = IntArray(1); GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS, ok, 0)
            check(ok[0] != 0) { GL.glGetShaderInfoLog(shader) }; return shader
        }
        val v = shader(GL.GL_VERTEX_SHADER, vertex); val f = shader(GL.GL_FRAGMENT_SHADER, fragment)
        val p = GL.glCreateProgram(); GL.glAttachShader(p, v); GL.glAttachShader(p, f); GL.glLinkProgram(p)
        val ok = IntArray(1); GL.glGetProgramiv(p, GL.GL_LINK_STATUS, ok, 0)
        check(ok[0] != 0) { GL.glGetProgramInfoLog(p) }
        GL.glDeleteShader(v); GL.glDeleteShader(f); return p
    }
    companion object {
        private fun floats(vararg values: Float): FloatBuffer = ByteBuffer.allocateDirect(values.size * 4)
            .order(ByteOrder.nativeOrder()).asFloatBuffer().apply { put(values); position(0) }
        private const val CAMERA_VERTEX = """
            attribute vec2 position; attribute vec2 uv; varying vec2 tex;
            void main() { gl_Position = vec4(position, 0.0, 1.0); tex = uv; }
        """
        private const val CAMERA_FRAGMENT = """
            #extension GL_OES_EGL_image_external : require
            precision mediump float; uniform samplerExternalOES camera; varying vec2 tex;
            void main() { gl_FragColor = texture2D(camera, tex); }
        """
        private const val WATER_VERTEX = """
            uniform mat4 mvp; uniform mat4 mv; attribute vec3 position; attribute vec3 surfaceNormal;
            varying vec3 pointLocal; varying vec3 normalLocal;
            varying vec2 waterCoord;
            varying vec2 local; varying float distanceM; uniform float patchSize;
            void main() { waterCoord=position.xz/patchSize+0.5; gl_Position = mvp * vec4(position, 1.0);
                distanceM = -(mv * vec4(position, 1.0)).z; local = position.xz; pointLocal=position; normalLocal=surfaceNormal; }
        """
        // Vertex displacement and texture normals ported from Evan Wallace's water renderer.
        private const val GPU_WATER_VERTEX = """
            precision highp float;
            uniform mat4 mvp;uniform mat4 mv;uniform float patchSize;uniform float referenceOnly;uniform float gpuWater;
            uniform highp sampler2D waterField;
            attribute vec3 position;attribute vec3 surfaceNormal;
            varying vec3 pointLocal;varying vec3 normalLocal;varying vec2 waterCoord;
            varying vec2 local;varying float distanceM;
            void main(){
                waterCoord=position.xz/patchSize+0.5;vec3 p=position;normalLocal=surfaceNormal;
                if(referenceOnly<0.5&&gpuWater>0.5){
                    vec4 info=texture2D(waterField,waterCoord);p.y+=info.r;
                    normalLocal=vec3(info.b,sqrt(max(0.0,1.0-dot(info.ba,info.ba))),info.a);
                }
                pointLocal=p;local=p.xz;distanceM=-(mv*vec4(p,1.0)).z;gl_Position=mvp*vec4(p,1.0);
            }
        """
        private const val WATER_FRAGMENT = """
            #extension GL_OES_EGL_image_external : require
            precision highp float;
            uniform samplerExternalOES cameraFeed;
            uniform mat4 mv;uniform mat4 mvp;
            uniform highp sampler2D waterField;uniform float gpuWater;uniform vec4 lightCorrection;
            varying vec2 waterCoord;
            uniform vec2 cameraOrigin; uniform vec2 cameraX; uniform vec2 cameraY;
            uniform vec3 eyeLocal;
            uniform float standalone; uniform float reportedDepth; uniform float halfExtent;
            varying vec3 pointLocal; varying vec3 normalLocal;
            uniform sampler2D depthImage; uniform float occlusion;
            uniform float referenceOnly; uniform vec2 viewport;
            uniform vec2 uvOrigin; uniform vec2 uvX; uniform vec2 uvY;
            varying vec2 local; varying float distanceM;
            vec3 floorColour(vec2 p) {
                if (max(abs(p.x),abs(p.y)) > halfExtent) return vec3(0.035,0.065,0.06);
                vec2 tilePosition=(p+halfExtent)*6.0/halfExtent;
                vec2 cell=fract(tilePosition);
                float line=step(0.025,min(min(cell.x,cell.y),min(1.0-cell.x,1.0-cell.y)));
                float tile=mod(floor(tilePosition.x)+floor(tilePosition.y),2.0);
                return mix(vec3(0.23,0.29,0.27),mix(vec3(0.55,0.61,0.56),vec3(0.65,0.69,0.63),tile),line);
            }
            void main() {
                if (referenceOnly > 2.5) { gl_FragColor=vec4(floorColour(local),1.0); return; }
                if (occlusion > 0.5) {
                    vec2 screen = gl_FragCoord.xy / viewport;
                    vec2 uv = uvOrigin + screen.x * uvX + screen.y * uvY;
                    vec4 depthSample = texture2D(depthImage, uv);
                    float realM = (depthSample.r * 255.0 + depthSample.a * 65280.0) * 0.001;
                    if (realM > 0.0 && distanceM > realM + 0.03) discard;
                }
                if (referenceOnly > 1.5) { gl_FragColor = vec4(1.0, 1.0, 1.0, 0.95); return; }
                float edge = max(abs(local.x), abs(local.y));
                if (referenceOnly > 0.5) {
                    if (edge < 1.45) discard;
                    gl_FragColor = vec4(0.45, 1.0, 0.65, 0.95); return;
                }
                // Heightfield normals drive reflection/refraction, adapted from Evan Wallace's MIT water demo.
                vec3 n=normalize(normalLocal);
                if(gpuWater>0.5){
                    vec2 coord=waterCoord;vec4 info=texture2D(waterField,coord);
                    for(int i=0;i<5;i++){coord+=info.ba*0.005;info=texture2D(waterField,coord);}
                    n=normalize(vec3(info.b,sqrt(max(0.0,1.0-dot(info.ba,info.ba))),info.a));
                }
                vec3 v=normalize(eyeLocal-pointLocal);
                bool above=dot(n,v)>=0.0;if(!above)n=-n;
                vec3 refractedRay=refract(-v,n,above?1.0/1.333:1.333);
                bool totalReflection=dot(refractedRay,refractedRay)<0.000001;
                float fresnel=0.025+0.975*pow(1.0-max(dot(n,v),0.0),5.0);
                vec2 screen=gl_FragCoord.xy/viewport;
                vec2 distorted=screen;
                // Intersect the transmitted ray with the confirmed reference plane.
                // Camera sampling remains an approximation for hidden/occluded content.
                if(!totalReflection&&abs(refractedRay.y)>0.001){
                    float travel=(-reportedDepth-pointLocal.y)/refractedRay.y;
                    vec4 hit=mvp*vec4(pointLocal+refractedRay*travel,1.0);
                    if(travel>=0.0&&travel<100.0&&hit.w>0.001)distorted=hit.xy/hit.w*0.5+0.5;
                }
                distorted=clamp(distorted,vec2(0.002),vec2(0.998));
                vec2 cameraUv=clamp(cameraOrigin+distorted.x*cameraX+distorted.y*cameraY,vec2(0.002),vec2(0.998));
                vec3 transmitted=texture2D(cameraFeed,cameraUv).rgb;
                if (standalone > 0.5) {
                    vec3 ray=refractedRay;
                    float travel=(-reportedDepth-pointLocal.y)/min(ray.y,-0.001);
                    transmitted=floorColour((pointLocal+ray*travel).xz);
                }
                transmitted=mix(transmitted,vec3(0.06,0.25,0.27),0.24);
                // Synthetic sky fallback: no claim of measured surrounding reflections.
                vec3 reflected=mix(vec3(0.24,0.38,0.43),vec3(0.75,0.84,0.86),clamp(reflect(-v,n).y,0.0,1.0));
                reflected*=lightCorrection.rgb*clamp(lightCorrection.a,0.1,1.5);
                vec3 halfLight=normalize(v+normalize(vec3(-0.4,1.0,0.3)));
                float highlight=pow(max(dot(n,halfLight),0.0),120.0)*0.45;
                vec3 colour=mix(transmitted,reflected,totalReflection?1.0:fresnel)+vec3(highlight)*lightCorrection.rgb*clamp(lightCorrection.a,0.1,1.5);
                gl_FragColor=vec4(colour,standalone>0.5?1.0:(edge>1.46?0.85:0.78));
            }
        """
    }
}
