package com.example.eso1.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

private enum class AscensionStage(
    val label: String,
    val instruction: String,
    val action: String
) {
    Scan("Scanning", "Sweep the room slowly. Let the locator catch a cold edge.", "Lock signal"),
    Lock("Signal Locked", "Hold the center over the shape. Keep the phone still.", "Begin rite"),
    Name("Naming", "Tap the seal three times. The room learns what is being released.", "Mark seal"),
    Release("Release", "Guide the shape upward. Keep your attention inside the ring.", "Send to light"),
    Complete("Clear", "The field is sealed. The room may be treated as reset.", "Restart")
}

@Composable
fun AscensionScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
        )
    }
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasCameraPermission = granted
    }
    var stage by remember { mutableStateOf(AscensionStage.Scan) }
    var sealTaps by remember { mutableStateOf(0) }

    val transition = rememberInfiniteTransition(label = "ascension")
    val phase by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(5200, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "phase"
    )

    LaunchedEffect(Unit) {
        if (!hasCameraPermission) {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        if (hasCameraPermission) {
            CameraPreviewLayer()
        } else {
            SimulatedCameraLayer(phase = phase)
        }

        AscensionOverlay(stage = stage, phase = phase)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 18.dp, vertical = 34.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TextButton(onClick = onBack) {
                    Text("Back")
                }
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    text = "Ascension",
                    color = Color.White,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.weight(1f))
                TextButton(onClick = {
                    hasCameraPermission = ContextCompat.checkSelfPermission(
                        context,
                        Manifest.permission.CAMERA
                    ) == PackageManager.PERMISSION_GRANTED
                    if (!hasCameraPermission) permissionLauncher.launch(Manifest.permission.CAMERA)
                }) {
                    Text("Camera")
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            RitualPanel(
                stage = stage,
                progress = (AscensionStage.entries.indexOf(stage) + sealTaps * 0.18f) / AscensionStage.entries.size,
                sealTaps = sealTaps,
                onAdvance = {
                    when (stage) {
                        AscensionStage.Scan -> stage = AscensionStage.Lock
                        AscensionStage.Lock -> stage = AscensionStage.Name
                        AscensionStage.Name -> {
                            val nextTaps = sealTaps + 1
                            sealTaps = nextTaps
                            if (nextTaps >= 3) {
                                sealTaps = 0
                                stage = AscensionStage.Release
                            }
                        }

                        AscensionStage.Release -> stage = AscensionStage.Complete
                        AscensionStage.Complete -> stage = AscensionStage.Scan
                    }
                }
            )
        }
    }
}

@Composable
private fun CameraPreviewLayer() {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val previewView = remember {
        PreviewView(context).apply {
            scaleType = PreviewView.ScaleType.FILL_CENTER
        }
    }

    DisposableEffect(lifecycleOwner) {
        val future = ProcessCameraProvider.getInstance(context)
        val executor = ContextCompat.getMainExecutor(context)
        future.addListener(
            {
                val cameraProvider = future.get()
                val preview = Preview.Builder().build().also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }
                runCatching {
                    cameraProvider.unbindAll()
                    cameraProvider.bindToLifecycle(
                        lifecycleOwner,
                        CameraSelector.DEFAULT_BACK_CAMERA,
                        preview
                    )
                }
            },
            executor
        )

        onDispose {
            if (future.isDone) {
                runCatching { future.get().unbindAll() }
            }
        }
    }

    AndroidView(
        factory = { previewView },
        modifier = Modifier.fillMaxSize()
    )
}

@Composable
private fun SimulatedCameraLayer(phase: Float) {
    Canvas(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF050509))
    ) {
        drawRect(
            brush = Brush.radialGradient(
                colors = listOf(Color(0xFF1F2937), Color(0xFF050509)),
                center = Offset(size.width * 0.55f, size.height * 0.35f),
                radius = size.maxDimension * 0.8f
            )
        )
        repeat(16) { index ->
            val y = size.height * (index / 15f)
            drawLine(
                color = Color.White.copy(alpha = 0.03f + sin(phase * PI.toFloat() * 2f + index) * 0.02f),
                start = Offset(0f, y),
                end = Offset(size.width, y + 24.dp.toPx()),
                strokeWidth = 1.dp.toPx()
            )
        }
    }
}

@Composable
private fun AscensionOverlay(stage: AscensionStage, phase: Float) {
    Canvas(modifier = Modifier.fillMaxSize()) {
        drawRect(Color(0xAA04060A))
        drawRect(
            brush = Brush.radialGradient(
                colors = listOf(Color.Transparent, Color(0xDD050509)),
                center = Offset(size.width / 2f, size.height * 0.46f),
                radius = size.minDimension * 0.78f
            )
        )

        val center = Offset(size.width / 2f, size.height * 0.45f)
        val lift = if (stage == AscensionStage.Release || stage == AscensionStage.Complete) phase * 120.dp.toPx() else 0f
        val marker = Offset(
            x = center.x + sin(phase * PI.toFloat() * 2f) * 34.dp.toPx(),
            y = center.y - lift + cos(phase * PI.toFloat() * 2f) * 18.dp.toPx()
        )
        val color = if (stage == AscensionStage.Complete) Color(0xFFFFF7D6) else Color(0xFFFFD166)

        repeat(4) { index ->
            drawCircle(
                color = color.copy(alpha = 0.12f - index * 0.02f),
                radius = 76.dp.toPx() + index * 34.dp.toPx() + sin(phase * PI.toFloat() * 2f) * 8.dp.toPx(),
                center = center,
                style = Stroke(width = 1.5.dp.toPx())
            )
        }

        repeat(38) { index ->
            val angle = index / 38f * PI.toFloat() * 2f + phase * PI.toFloat() * 2f
            val inner = 118.dp.toPx()
            val outer = inner + 16.dp.toPx() + sin(angle * 3f) * 7.dp.toPx()
            drawLine(
                color = color.copy(alpha = 0.44f),
                start = Offset(center.x + cos(angle) * inner, center.y + sin(angle) * inner),
                end = Offset(center.x + cos(angle) * outer, center.y + sin(angle) * outer),
                strokeWidth = 2.dp.toPx()
            )
        }

        val ghostPath = Path().apply {
            moveTo(marker.x, marker.y - 52.dp.toPx())
            cubicTo(marker.x - 46.dp.toPx(), marker.y - 28.dp.toPx(), marker.x - 35.dp.toPx(), marker.y + 50.dp.toPx(), marker.x, marker.y + 42.dp.toPx())
            cubicTo(marker.x + 35.dp.toPx(), marker.y + 50.dp.toPx(), marker.x + 46.dp.toPx(), marker.y - 28.dp.toPx(), marker.x, marker.y - 52.dp.toPx())
        }
        drawPath(
            path = ghostPath,
            color = color.copy(alpha = if (stage == AscensionStage.Complete) 0.18f else 0.62f),
            style = Stroke(width = 3.dp.toPx())
        )
        drawCircle(
            color = color.copy(alpha = if (stage == AscensionStage.Complete) 0.16f else 0.32f),
            radius = 48.dp.toPx(),
            center = marker
        )

        if (stage == AscensionStage.Complete) {
            drawRect(
                brush = Brush.verticalGradient(
                    colors = listOf(Color(0x88FFF7D6), Color.Transparent),
                    startY = 0f,
                    endY = size.height
                )
            )
        }
    }
}

@Composable
private fun RitualPanel(
    stage: AscensionStage,
    progress: Float,
    sealTaps: Int,
    onAdvance: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xDD0B0E14), RoundedCornerShape(8.dp))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = stage.label.uppercase(),
            color = Color(0xFFFFD166),
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Black
        )
        Text(
            text = stage.instruction,
            color = Color.White,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        LinearProgressIndicator(
            progress = { progress.coerceIn(0f, 1f) },
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp),
            color = Color(0xFFFFD166),
            trackColor = Color(0xFF272B36)
        )
        Button(
            onClick = onAdvance,
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(8.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFFFFD166),
                contentColor = Color(0xFF171004)
            )
        ) {
            Text(
                text = if (stage == AscensionStage.Name) "${stage.action} ${sealTaps + 1}/3" else stage.action,
                fontWeight = FontWeight.Black
            )
        }
    }
}
