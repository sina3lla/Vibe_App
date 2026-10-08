package com.example.eso1.ui.engine

import android.content.Context
import android.view.Choreographer
import android.view.Surface
import android.view.SurfaceView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTagsAsResourceId
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.google.android.filament.Camera
import com.google.android.filament.Engine
import com.google.android.filament.Renderer
import com.google.android.filament.Scene
import com.google.android.filament.Skybox
import com.google.android.filament.SwapChain
import com.google.android.filament.Viewport
import com.google.android.filament.android.DisplayHelper
import com.google.android.filament.android.UiHelper
import com.google.android.filament.View as FilamentView

/**
 * Proves the Filament rendering pipeline mounts and draws inside the existing Compose shell
 * (see docs/decisions/3D_ENGINE_EVALUATION.md). It intentionally shows an ambient idle colour
 * field rather than a lit mesh: RenderableManager geometry needs a compiled Filament material
 * (matc at build time, or the filamat-android runtime material builder), and this milestone's
 * dependency scope is exactly filament-android. That gap is this harness's one open follow-up,
 * not something to fake with hand-authored binary material bytes.
 *
 * The scene renders once per surface/size change, never on a continuous loop, so it is
 * inherently idle and needs no reduce-motion branching of its own. The non-spatial fallback
 * stays reachable even when the native renderer never becomes available.
 */
@Composable
fun EngineHarness(modifier: Modifier = Modifier) {
    val filamentAvailable = remember { probeFilamentAvailability() }
    var showFallback by rememberSaveable { mutableStateOf(!filamentAvailable) }

    Column(
        modifier = modifier
            .fillMaxWidth()
            .semantics { testTagsAsResourceId = true }
    ) {
        Text(
            text = "Engine preview",
            color = Color.White,
            style = MaterialTheme.typography.titleMedium
        )
        Text(
            text = "A still, ambient scene proving the 3D pipeline renders here.",
            color = Color(0xFFB7BBC8),
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.padding(top = 2.dp, bottom = 10.dp)
        )

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(160.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(Color(0xFF0E1118))
                .testTag("engine-canvas"),
            contentAlignment = Alignment.Center
        ) {
            if (showFallback || !filamentAvailable) {
                Text(
                    text = "Non-spatial description: a single still field of deep violet " +
                        "light, with no motion required to understand it.",
                    color = Color(0xFFE5E7EB),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(16.dp)
                )
            } else {
                FilamentCanvas(modifier = Modifier.fillMaxWidth().height(160.dp))
            }
        }

        if (filamentAvailable) {
            TextButton(onClick = { showFallback = !showFallback }) {
                Text(
                    text = if (showFallback) "Switch to 3D scene" else "Switch to text description",
                    color = MaterialTheme.colorScheme.primary
                )
            }
        } else {
            Text(
                text = "3D rendering isn't available on this device; showing the description instead.",
                color = Color(0xFF6B7080),
                style = MaterialTheme.typography.labelMedium,
                modifier = Modifier.padding(top = 4.dp)
            )
        }
    }
}

private fun probeFilamentAvailability(): Boolean = try {
    val engine = Engine.create()
    engine.destroy()
    true
} catch (_: Throwable) {
    false
}

@Composable
private fun FilamentCanvas(modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { context -> FilamentSurfaceView(context) },
        onRelease = { view -> (view as? FilamentSurfaceView)?.release() }
    )
}

private class FilamentSurfaceView(context: Context) : SurfaceView(context) {

    private var healthy = true
    private val engine: Engine? = runCatching { Engine.create() }.getOrNull()
    private var renderer: Renderer? = null
    private var scene: Scene? = null
    private var camera: Camera? = null
    private var cameraEntity: Int = 0
    private var filamentView: FilamentView? = null
    private var skybox: Skybox? = null
    private var swapChain: SwapChain? = null
    private var uiHelper: UiHelper? = null
    private var displayHelper: DisplayHelper? = null

    init {
        val currentEngine = engine
        if (currentEngine == null) {
            healthy = false
        } else {
            try {
                val currentRenderer = currentEngine.createRenderer()
                val currentScene = currentEngine.createScene()
                val entity = com.google.android.filament.EntityManager.get().create()
                val currentCamera = currentEngine.createCamera(entity)
                val currentView = currentEngine.createView()
                val currentSkybox = Skybox.Builder()
                    .color(0.09f, 0.03f, 0.18f, 1f)
                    .build(currentEngine)

                currentScene.setSkybox(currentSkybox)
                currentView.setScene(currentScene)
                currentView.setCamera(currentCamera)

                renderer = currentRenderer
                scene = currentScene
                cameraEntity = entity
                camera = currentCamera
                filamentView = currentView
                skybox = currentSkybox

                val helper = UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK)
                helper.setRenderCallback(object : UiHelper.RendererCallback {
                    override fun onNativeWindowChanged(surface: Surface) {
                        swapChain?.let { currentEngine.destroySwapChain(it) }
                        swapChain = currentEngine.createSwapChain(surface)
                        displayHelper?.attach(currentRenderer, display)
                        renderOnce()
                    }

                    override fun onDetachedFromSurface() {
                        swapChain?.let {
                            currentEngine.destroySwapChain(it)
                            currentEngine.flushAndWait()
                        }
                        swapChain = null
                    }

                    override fun onResized(width: Int, height: Int) {
                        val aspect = width.toDouble() / height.toDouble().coerceAtLeast(1.0)
                        currentCamera.setProjection(
                            45.0,
                            aspect,
                            0.1,
                            20.0,
                            Camera.Fov.VERTICAL
                        )
                        currentView.setViewport(Viewport(0, 0, width, height))
                        renderOnce()
                    }
                })
                displayHelper = DisplayHelper(context)
                uiHelper = helper
                helper.attachTo(this)
            } catch (_: Throwable) {
                healthy = false
            }
        }
    }

    private fun renderOnce() {
        val currentEngine = engine ?: return
        val currentRenderer = renderer ?: return
        val currentView = filamentView ?: return
        val chain = swapChain ?: return
        val helper = uiHelper ?: return
        Choreographer.getInstance().postFrameCallback(object : Choreographer.FrameCallback {
            override fun doFrame(frameTimeNanos: Long) {
                if (helper.isReadyToRender) {
                    if (currentRenderer.beginFrame(chain, frameTimeNanos)) {
                        currentRenderer.render(currentView)
                        currentRenderer.endFrame()
                    }
                }
            }
        })
    }

    fun release() {
        val currentEngine = engine ?: return
        try {
            uiHelper?.detach()
            if (healthy) {
                swapChain?.let { currentEngine.destroySwapChain(it) }
                renderer?.let { currentEngine.destroyRenderer(it) }
                filamentView?.let { currentEngine.destroyView(it) }
                skybox?.let { currentEngine.destroySkybox(it) }
                scene?.let { currentEngine.destroyScene(it) }
                if (cameraEntity != 0) {
                    currentEngine.destroyCameraComponent(cameraEntity)
                    com.google.android.filament.EntityManager.get().destroy(cameraEntity)
                }
            }
            currentEngine.destroy()
        } catch (_: Throwable) {
            // Best-effort teardown: a native resource released out of Filament's preferred
            // order must not crash the host Activity on recomposition/disposal.
        }
    }
}
