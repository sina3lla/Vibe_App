package com.example.eso1.ui.engine

import android.content.Context
import android.view.Choreographer
import android.view.Surface
import android.view.SurfaceView
import android.view.View
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTagsAsResourceId
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.example.eso1.ui.theme.Cyan80
import com.example.eso1.ui.theme.Gold80
import com.example.eso1.ui.theme.Violet80
import com.google.android.filament.Camera
import com.google.android.filament.Engine
import com.google.android.filament.Renderer
import com.google.android.filament.Scene
import com.google.android.filament.Skybox
import com.google.android.filament.SwapChain
import com.google.android.filament.Viewport
import com.google.android.filament.android.DisplayHelper
import com.google.android.filament.android.UiHelper
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt
import com.google.android.filament.View as FilamentView

/**
 * Proves the Filament rendering pipeline mounts inside the existing Compose shell (see
 * docs/decisions/3D_ENGINE_EVALUATION.md) and shows a real low-poly object.
 *
 * Known blocker, reported honestly rather than papered over: Filament's own
 * `RenderableManager` needs a compiled `.filamat` material produced by running `matc`
 * (a standalone binary, not a Gradle task) outside this project, and this implementing
 * session only has file tools — there is no shell step available to run `matc` or to
 * verify a hand-authored binary material payload against this exact Filament build.
 * Per CURRENT_TASK's own contingency, this harness therefore renders the required real
 * geometry (a shaded, rotatable cube) as the "best non-plugin substitute" using ordinary
 * Compose `Canvas` drawing — plain 3D-to-2D math, no native renderer involved — layered
 * over the Filament surface, which still independently proves the native pipeline mounts
 * and draws (its skybox) in this shell. Follow-up to raise with the owner/controller: a
 * small scoped milestone to run `matc` once (or evaluate the gltfio ubershader path) and
 * commit a compiled material asset, so the cube can move onto real Filament geometry.
 *
 * The cube only rotates in fixed, discrete steps on an explicit tap — never continuously
 * on its own — so there is no reduce-motion branch to add: the idle state already has no
 * required animation. The text/non-spatial fallback is a separate toggle, reachable and
 * meaningful whether or not the native surface or the cube renders at all.
 */
@Composable
fun EngineHarness(modifier: Modifier = Modifier) {
    val filamentAvailable = remember { probeFilamentAvailability() }
    var showFallback by rememberSaveable { mutableStateOf(false) }
    var rotationStep by rememberSaveable { mutableIntStateOf(0) }

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
            text = "A small object proving the 3D pipeline renders here.",
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
                .testTag("engine-canvas")
                .then(
                    if (showFallback) {
                        Modifier.semantics {
                            contentDescription = "Non-spatial description of the object."
                        }
                    } else {
                        Modifier
                            .clickable { rotationStep = (rotationStep + 1) % CUBE_ROTATION_STEPS }
                            .semantics {
                                contentDescription = "A small glowing cube. Tap to turn it."
                            }
                    }
                ),
            contentAlignment = Alignment.Center
        ) {
            if (showFallback) {
                Text(
                    text = "Non-spatial description: a single still cube of violet, cyan, " +
                        "and gold light, with no motion required to understand it.",
                    color = Color(0xFFE5E7EB),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(16.dp)
                )
            } else {
                if (filamentAvailable) {
                    FilamentCanvas(modifier = Modifier.fillMaxSize())
                }
                Canvas(modifier = Modifier.fillMaxSize().clearAndSetSemantics {}) {
                    drawMagicalCube(this, rotationStep)
                }
            }
        }

        TextButton(onClick = { showFallback = !showFallback }) {
            Text(
                text = if (showFallback) "Switch to 3D scene" else "Switch to text description",
                color = MaterialTheme.colorScheme.primary
            )
        }
        if (!filamentAvailable) {
            Text(
                text = "Native 3D pipeline unavailable on this device; the object above is " +
                    "shown without it.",
                color = Color(0xFF6B7080),
                style = MaterialTheme.typography.labelMedium,
                modifier = Modifier.padding(top = 4.dp)
            )
        }
    }
}

private const val CUBE_ROTATION_STEPS = 8

private data class Vec3(val x: Float, val y: Float, val z: Float)

private fun rotateY(v: Vec3, radians: Float): Vec3 {
    val c = cos(radians)
    val s = sin(radians)
    return Vec3(v.x * c + v.z * s, v.y, -v.x * s + v.z * c)
}

private fun rotateX(v: Vec3, radians: Float): Vec3 {
    val c = cos(radians)
    val s = sin(radians)
    return Vec3(v.x, v.y * c - v.z * s, v.y * s + v.z * c)
}

private fun dot(a: Vec3, b: Vec3): Float = a.x * b.x + a.y * b.y + a.z * b.z

private fun normalize(v: Vec3): Vec3 {
    val length = sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
    return if (length == 0f) v else Vec3(v.x / length, v.y / length, v.z / length)
}

private val CUBE_VERTICES = listOf(
    Vec3(-0.5f, -0.5f, -0.5f),
    Vec3(0.5f, -0.5f, -0.5f),
    Vec3(0.5f, 0.5f, -0.5f),
    Vec3(-0.5f, 0.5f, -0.5f),
    Vec3(-0.5f, -0.5f, 0.5f),
    Vec3(0.5f, -0.5f, 0.5f),
    Vec3(0.5f, 0.5f, 0.5f),
    Vec3(-0.5f, 0.5f, 0.5f)
)

private data class CubeFace(val indices: IntArray, val normal: Vec3, val baseColor: Color)

private val CUBE_FACES = listOf(
    CubeFace(intArrayOf(4, 5, 6, 7), Vec3(0f, 0f, 1f), Gold80),
    CubeFace(intArrayOf(1, 0, 3, 2), Vec3(0f, 0f, -1f), Gold80),
    CubeFace(intArrayOf(5, 1, 2, 6), Vec3(1f, 0f, 0f), Violet80),
    CubeFace(intArrayOf(0, 4, 7, 3), Vec3(-1f, 0f, 0f), Violet80),
    CubeFace(intArrayOf(7, 6, 2, 3), Vec3(0f, 1f, 0f), Cyan80),
    CubeFace(intArrayOf(0, 1, 5, 4), Vec3(0f, -1f, 0f), Cyan80)
)

private val LIGHT_DIRECTION = normalize(Vec3(0.5f, 0.8f, 0.35f))
private const val TILT_RADIANS = -0.42f
private const val CAMERA_DISTANCE = 2.6f

private fun drawMagicalCube(drawScope: DrawScope, rotationStep: Int) {
    val turn = rotationStep * (2f * Math.PI.toFloat() / CUBE_ROTATION_STEPS)
    val rotatedVertices = CUBE_VERTICES.map { rotateX(rotateY(it, turn), TILT_RADIANS) }

    val scale = drawScope.size.minDimension * 0.42f
    val centerX = drawScope.size.width / 2f
    val centerY = drawScope.size.height / 2f

    fun project(v: Vec3): Offset {
        val perspective = CAMERA_DISTANCE / (CAMERA_DISTANCE - v.z)
        return Offset(centerX + v.x * perspective * scale, centerY - v.y * perspective * scale)
    }

    val orderedFaces = CUBE_FACES.sortedBy { face ->
        face.indices.map { rotatedVertices[it].z }.average()
    }

    for (face in orderedFaces) {
        val rotatedNormal = rotateX(rotateY(face.normal, turn), TILT_RADIANS)
        val brightness = (dot(rotatedNormal, LIGHT_DIRECTION).coerceIn(0f, 1f) * 0.75f + 0.25f)
        val shaded = Color(
            red = (face.baseColor.red * brightness).coerceIn(0f, 1f),
            green = (face.baseColor.green * brightness).coerceIn(0f, 1f),
            blue = (face.baseColor.blue * brightness).coerceIn(0f, 1f),
            alpha = 1f
        )

        val points = face.indices.map { project(rotatedVertices[it]) }
        val path = Path().apply {
            moveTo(points[0].x, points[0].y)
            for (i in 1 until points.size) {
                lineTo(points[i].x, points[i].y)
            }
            close()
        }
        drawScope.drawPath(path, color = shaded)
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
    // The native surface is decorative background only; the Box that hosts it (engine-canvas)
    // carries the real description and click action, so TalkBack must skip this opaque render
    // rather than stop on an unlabeled native node.
    AndroidView(
        modifier = modifier.clearAndSetSemantics {},
        factory = { context ->
            FilamentSurfaceView(context).apply {
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }
        },
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
