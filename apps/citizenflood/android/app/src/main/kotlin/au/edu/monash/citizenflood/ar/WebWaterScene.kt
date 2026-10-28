package au.edu.monash.citizenflood.ar

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Color
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.ViewGroup
import android.webkit.*
import java.io.ByteArrayInputStream
import org.json.JSONObject

/** Offline, origin-restricted GPU renderer. Deliberately exposes no JavascriptInterface. */
@SuppressLint("SetJavaScriptEnabled")
class WebWaterScene(context: Context, depthM: Float, private val ready: () -> Unit,
                    private val failed: () -> Unit) : WaterScene {
    private val handler=Handler(Looper.getMainLooper())
    private var destroyed=false
    private var loaded=false
    private var foreground=false
    private val startupTimeout=Runnable { if(!loaded&&!destroyed)failed() }
    private val web=WebView(context)
    override val view=web
    init {
        if (context.applicationInfo.flags and android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE != 0)
            WebView.setWebContentsDebuggingEnabled(true)
        web.setBackgroundColor(Color.rgb(11,23,24))
        web.contentDescription="Illustrative water. Tap for ripples, drag to rotate, pinch to zoom."
        web.settings.apply {
            javaScriptEnabled=true;allowFileAccess=false;allowContentAccess=false
            blockNetworkLoads=true;domStorageEnabled=false;databaseEnabled=false
            javaScriptCanOpenWindowsAutomatically=false;setSupportMultipleWindows(false)
            mixedContentMode=WebSettings.MIXED_CONTENT_NEVER_ALLOW
            cacheMode=WebSettings.LOAD_NO_CACHE;mediaPlaybackRequiresUserGesture=true
        }
        CookieManager.getInstance().setAcceptThirdPartyCookies(web,false)
        web.webViewClient=object:WebViewClient(){
            override fun shouldOverrideUrlLoading(view:WebView,request:WebResourceRequest)=true
            override fun shouldInterceptRequest(view:WebView,request:WebResourceRequest):WebResourceResponse {
                val path=WaterAssetPolicy.path(request.url.toString())
                if(request.method!="GET"||path==null)return blocked()
                return try {
                    val mime=when(path.substringAfterLast('.')){"html"->"text/html";"css"->"text/css";else->"application/javascript"}
                    WebResourceResponse(mime,"UTF-8",200,"OK",mapOf("Cache-Control" to "no-store"),context.assets.open(path))
                }catch(_:Exception){blocked()}
            }
            override fun onReceivedError(view:WebView,request:WebResourceRequest,error:WebResourceError){
                if(!destroyed&&request.isForMainFrame)failed()
            }
            override fun onRenderProcessGone(view:WebView,detail:RenderProcessGoneDetail):Boolean {
                if(!destroyed)failed();return true
            }
        }
        web.webChromeClient=object:WebChromeClient(){
            override fun onConsoleMessage(message:ConsoleMessage):Boolean {
                if(destroyed||!message.sourceId().startsWith(WaterAssetPolicy.ORIGIN+"/"))return true
                when {
                    message.message()=="WATER_READY"->{
                        loaded=true;handler.removeCallbacks(startupTimeout)
                        if(!foreground)command("background")
                        Log.i("WaterPreview","Full GPU water renderer ready");ready()
                    }
                    message.message().startsWith("WATER_ERROR:")->{
                        Log.w("WaterPreview",message.message().take(200));handler.post { if(!destroyed)failed() }
                    }
                    message.message().startsWith("WATER_STATS:")->Log.i("WaterPreview",message.message().take(300))
                }
                return true
            }
            override fun onPermissionRequest(request:PermissionRequest){request.deny()}
        }
        handler.postDelayed(startupTimeout,15000)
        web.loadUrl("${WaterAssetPolicy.ORIGIN}/index.html?depthM=$depthM")
    }
    private fun blocked()=WebResourceResponse("text/plain","UTF-8",403,"Blocked",emptyMap(),ByteArrayInputStream(ByteArray(0)))
    override fun command(name:String){
        if(destroyed)return
        web.evaluateJavascript("window.waterPreview && window.waterPreview.command(${JSONObject.quote(name)})",null)
    }
    override fun resume(){
        if(destroyed)return;foreground=true;web.onResume();if(loaded)command("foreground")
    }
    override fun pause(){
        if(destroyed)return;foreground=false;if(loaded)command("background");web.onPause()
    }
    override fun destroy(){
        if(destroyed)return;destroyed=true;handler.removeCallbacks(startupTimeout)
        (web.parent as? ViewGroup)?.removeView(web)
        web.stopLoading();web.onPause();web.removeAllViews();web.destroy()
    }
}
