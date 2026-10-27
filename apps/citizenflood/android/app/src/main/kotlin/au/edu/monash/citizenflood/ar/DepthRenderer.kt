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
) : GLSurfaceView.Renderer {
    @Volatile var session: Session? = null
    @Volatile var rotation: Int = 0
    private var width = 1
    private var height = 1
    private val pendingTap = AtomicReference<Pair<Float, Float>?>(null)
    private var anchor: Anchor? = null
    private var confirmed = false
    private var cameraTexture = 0
    private var depthTexture = 0
    private var cameraProgram = 0
    private var waterProgram = 0
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

    fun tap(x: Float, y: Float) { pendingTap.set(x to y) }
    fun confirmReference() {
        if (anchor?.trackingState == TrackingState.TRACKING) {
            confirmed = true; candidateChanged(false)
        }
    }
    fun reset() {
        anchor?.detach(); anchor = null; confirmed = false
        pendingTap.set(null); candidateChanged(false)
    }

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        try {
            GL.glClearColor(0f, 0f, 0f, 1f)
            cameraTexture = texture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES)
            depthTexture = texture(GL.GL_TEXTURE_2D)
            textureSession = null
            cameraProgram = program(CAMERA_VERTEX, CAMERA_FRAGMENT)
            waterProgram = program(WATER_VERTEX, WATER_FRAGMENT)
        } catch (_: Exception) { failed() }
    }
    override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) {
        width = w; height = h; GL.glViewport(0, 0, w, h)
    }
    override fun onDrawFrame(gl: GL10?) {
        GL.glClear(GL.GL_COLOR_BUFFER_BIT or GL.GL_DEPTH_BUFFER_BIT)
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
                pendingTap.set(null); candidateChanged(false)
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
                candidateChanged(false)
                status("Reference tracking lost. Move slowly or reset the reference."); return
            }
            camera.getViewMatrix(view, 0)
            camera.getProjectionMatrix(projection, 0, 0.05f, 100f)
            placed.pose.toMatrix(model, 0)
            if (!confirmed) {
                candidateChanged(true)
                drawWater(frame, false, true)
                status("Reference selected: outlined 3 m patch. Confirm it matches your described surface.")
                return
            }
            updateDepth(frame)
            drawWater(frame, frameDepthAvailable, false)
            status(if (frameDepthAvailable)
                "Local illustration · depth occlusion active. Reset if the reference drifts."
                else "Simplified preview · real objects may overlap virtual water.")
        } catch (_: Exception) { failed() }
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
                val size = image.width * image.height * 2
                var packed = depthBytes
                if (packed == null || packed.capacity() != size) {
                    packed = ByteBuffer.allocateDirect(size); depthBytes = packed
                }
                packed.clear()
                val start = source.position()
                for (y in 0 until image.height) for (x in 0 until image.width) {
                    val offset = start + y * plane.rowStride + x * plane.pixelStride
                    packed.put(source.get(offset)); packed.put(source.get(offset + 1))
                }
                packed.flip()
                GL.glActiveTexture(GL.GL_TEXTURE1)
                GL.glBindTexture(GL.GL_TEXTURE_2D, depthTexture)
                GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_LUMINANCE_ALPHA,
                    image.width, image.height, 0, GL.GL_LUMINANCE_ALPHA, GL.GL_UNSIGNED_BYTE, packed)
                frameDepthAvailable = true
            }
        } catch (_: NotYetAvailableException) { /* No stale depth from an earlier frame. */ }
        catch (_: java.lang.IllegalStateException) { /* Depth unsupported. */ }
    }

    private fun drawWater(frame: Frame, occlude: Boolean, referenceOnly: Boolean) {
        GL.glUseProgram(waterProgram)
        GL.glEnable(GL.GL_BLEND); GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        // A selected reference is drawn at ground height; confirmed water uses reported depth.
        if (!referenceOnly) Matrix.translateM(model, 0, 0f, depthM, 0f)
        Matrix.multiplyMM(mv, 0, view, 0, model, 0)
        Matrix.multiplyMM(mvp, 0, projection, 0, mv, 0)
        uniformMatrix("mvp", mvp); uniformMatrix("mv", mv)
        GL.glUniform1f(location("time"), (frame.timestamp % 60_000_000_000L) / 1_000_000_000f)
        GL.glUniform1f(location("referenceOnly"), if (referenceOnly) 1f else 0f)
        GL.glUniform1f(location("occlusion"), if (occlude) 1f else 0f)
        GL.glUniform2f(location("viewport"), width.toFloat(), height.toFloat())
        // ARCore's mapping is affine for this un-stabilised camera image.
        val u = FloatArray(8); imageUv.position(0); imageUv.get(u); imageUv.position(0)
        GL.glUniform2f(location("uvOrigin"), u[0], u[1])
        GL.glUniform2f(location("uvX"), u[2] - u[0], u[3] - u[1])
        GL.glUniform2f(location("uvY"), u[4] - u[0], u[5] - u[1])
        GL.glActiveTexture(GL.GL_TEXTURE1); GL.glBindTexture(GL.GL_TEXTURE_2D, depthTexture)
        GL.glUniform1i(location("depthImage"), 1)
        attribute(waterProgram, "position", quad, 3)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
        disableAttributes(waterProgram, "position")
        if (!referenceOnly) drawRuler()
        GL.glDisable(GL.GL_BLEND)
    }

    private fun drawRuler() {
        // A vertical scale beside the bounded patch; ticks every 10 cm, up to 100 ticks.
        val verts = ArrayList<Float>()
        fun point(x: Float, y: Float) { verts.add(x); verts.add(y); verts.add(0f) }
        point(0f, -depthM); point(0f, 0f)
        val count = minOf((depthM / 0.1f).toInt(), 100)
        for (i in 0..count) {
            val y = -depthM + i * 0.1f
            point(-0.035f, y); point(0.035f, y)
        }
        GL.glUniform1f(location("referenceOnly"), 2f)
        attribute(waterProgram, "position", floats(*verts.toFloatArray()), 3)
        GL.glLineWidth(2f)
        GL.glDrawArrays(GL.GL_LINES, 0, verts.size / 3)
        disableAttributes(waterProgram, "position")
    }
    private fun location(name: String) = GL.glGetUniformLocation(waterProgram, name)
    private fun uniformMatrix(name: String, matrix: FloatArray) =
        GL.glUniformMatrix4fv(location(name), 1, false, matrix, 0)
    private fun attribute(program: Int, name: String, data: FloatBuffer, size: Int) {
        val loc = GL.glGetAttribLocation(program, name)
        data.position(0); GL.glEnableVertexAttribArray(loc)
        GL.glVertexAttribPointer(loc, size, GL.GL_FLOAT, false, 0, data)
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
            uniform mat4 mvp; uniform mat4 mv; attribute vec3 position;
            varying vec2 local; varying float distanceM;
            void main() { gl_Position = mvp * vec4(position, 1.0);
                distanceM = -(mv * vec4(position, 1.0)).z; local = position.xz; }
        """
        private const val WATER_FRAGMENT = """
            precision highp float;
            uniform sampler2D depthImage; uniform float occlusion; uniform float time;
            uniform float referenceOnly; uniform vec2 viewport;
            uniform vec2 uvOrigin; uniform vec2 uvX; uniform vec2 uvY;
            varying vec2 local; varying float distanceM;
            void main() {
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
                float waves = sin(local.x * 15.0 + time * 1.5) *
                    sin(local.y * 12.0 - time * 1.1);
                vec3 colour = mix(vec3(0.04, 0.30, 0.37), vec3(0.25, 0.60, 0.63), waves * 0.5 + 0.5);
                gl_FragColor = vec4(colour, edge > 1.46 ? 0.9 : 0.58);
            }
        """
    }
}
