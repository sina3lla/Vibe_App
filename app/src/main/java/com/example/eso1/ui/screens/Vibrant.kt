package com.example.eso1.ui.screens

import androidx.compose.animation.animateColorAsState
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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.example.eso1.audio.RitualToneEngine
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun VibrantScreen(onBack: () -> Unit) {
    var active by remember { mutableStateOf(false) }
    var showExplanation by remember { mutableStateOf(false) }
    var intensity by remember { mutableFloatStateOf(0.54f) }
    var tone by remember { mutableFloatStateOf(0.36f) }
    var speed by remember { mutableFloatStateOf(0.48f) }
    val toneEngine = remember { RitualToneEngine() }

    val transition = rememberInfiniteTransition(label = "vibrant")
    val phase by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween((7600 - speed * 4300).toInt(), easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "phase"
    )
    val bg by animateColorAsState(
        targetValue = if (active) Color(0xFF081923) else Color(0xFF05070B),
        animationSpec = tween(900),
        label = "background"
    )

    LaunchedEffect(active, intensity, tone) {
        if (active) {
            toneEngine.start(baseFrequency = 82f + tone * 240f, intensity = intensity)
        } else {
            toneEngine.stop()
        }
    }

    DisposableEffect(Unit) {
        onDispose { toneEngine.stop() }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(bg)
            .padding(horizontal = 18.dp, vertical = 34.dp)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val glow = if (active) 0.42f else 0.16f
            drawRect(
                brush = Brush.radialGradient(
                    colors = listOf(Color(0xFF22D3EE).copy(alpha = glow), Color.Transparent),
                    center = Offset(size.width / 2f, size.height * 0.47f),
                    radius = size.minDimension * (0.72f + intensity * 0.18f)
                )
            )
            drawRect(
                brush = Brush.verticalGradient(
                    colors = listOf(Color.Transparent, Color(0x2214B8A6), Color.Transparent)
                )
            )
        }

        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally
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
                    text = "Vibrant",
                    color = Color.White,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.weight(1f))
                TextButton(onClick = { showExplanation = true }) {
                    Text("Explain")
                }
            }

            Spacer(modifier = Modifier.height(34.dp))

            Text(
                text = if (active) "ROOM FIELD ACTIVE" else "ROOM FIELD IDLE",
                color = if (active) Color(0xFF67E8F9) else Color(0xFF8D95A5),
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold
            )

            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                VibrantRing(
                    active = active,
                    phase = phase,
                    intensity = intensity,
                    speed = speed,
                    modifier = Modifier.size(310.dp)
                )
            }

            Button(
                onClick = { active = !active },
                modifier = Modifier
                    .size(160.dp)
                    .clip(CircleShape),
                shape = CircleShape,
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (active) Color(0xFFEFFBFF) else Color(0xFF111827),
                    contentColor = if (active) Color(0xFF082F49) else Color(0xFF67E8F9)
                )
            ) {
                Text(
                    text = if (active) "SEAL" else "BEGIN",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Black
                )
            }

            Spacer(modifier = Modifier.height(22.dp))

            ControlPanel(
                intensity = intensity,
                tone = tone,
                speed = speed,
                onIntensity = { intensity = it },
                onTone = { tone = it },
                onSpeed = { speed = it }
            )
        }
    }

    if (showExplanation) {
        AlertDialog(
            onDismissRequest = { showExplanation = false },
            confirmButton = {
                TextButton(onClick = { showExplanation = false }) {
                    Text("Close")
                }
            },
            title = { Text("How Vibrant Works") },
            text = {
                Text(
                    text = "Vibrant is a sensory ritual interface. The moving ring, low tone, and shifting color field give your attention one object to follow while you reset the feeling of a room. It does not measure energy or prove a room changed; it creates a focused moment that can make the space feel newly marked."
                )
            },
            containerColor = Color(0xFF11131B),
            titleContentColor = Color.White,
            textContentColor = Color(0xFFD6DAE3)
        )
    }
}

@Composable
private fun VibrantRing(
    active: Boolean,
    phase: Float,
    intensity: Float,
    speed: Float,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val center = Offset(size.width / 2f, size.height / 2f)
        val baseRadius = size.minDimension * 0.36f
        val segments = 132
        val pulse = if (active) 1f else 0.35f

        drawCircle(
            color = Color(0xFF22D3EE).copy(alpha = 0.07f + intensity * 0.18f),
            radius = baseRadius * (1.15f + sin(phase * PI.toFloat() * 2f) * 0.04f),
            center = center
        )

        for (index in 0 until segments) {
            val fraction = index / segments.toFloat()
            val angle = fraction * PI.toFloat() * 2f
            val wave = sin(angle * (5f + speed * 7f) + phase * PI.toFloat() * 2f)
            val surge = sin(angle * 2f - phase * PI.toFloat() * 4f)
            val length = (8.dp.toPx() + (wave + 1f) * 8.dp.toPx() * intensity + surge * 3.dp.toPx()) * pulse
            val radius = baseRadius + wave * 8.dp.toPx() * intensity
            val inner = Offset(center.x + cos(angle) * radius, center.y + sin(angle) * radius)
            val outer = Offset(center.x + cos(angle) * (radius + length), center.y + sin(angle) * (radius + length))
            drawLine(
                color = Color(0xFF22D3EE).copy(alpha = 0.42f + 0.5f * pulse),
                start = inner,
                end = outer,
                strokeWidth = 2.dp.toPx()
            )
        }

        drawCircle(
            color = Color.White.copy(alpha = if (active) 0.78f else 0.22f),
            radius = baseRadius * 0.94f,
            center = center,
            style = Stroke(width = 1.dp.toPx())
        )
    }
}

@Composable
private fun ControlPanel(
    intensity: Float,
    tone: Float,
    speed: Float,
    onIntensity: (Float) -> Unit,
    onTone: (Float) -> Unit,
    onSpeed: (Float) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xA60D1118), RoundedCornerShape(8.dp))
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        RitualSlider("Intensity", intensity, onIntensity)
        RitualSlider("Tone", tone, onTone)
        RitualSlider("Speed", speed, onSpeed)
    }
}

@Composable
private fun RitualSlider(label: String, value: Float, onValue: (Float) -> Unit) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = label,
                color = Color(0xFFE5E7EB),
                style = MaterialTheme.typography.labelLarge,
                modifier = Modifier.weight(1f)
            )
            Text(
                text = "${(value * 100).toInt()}",
                color = Color(0xFF67E8F9),
                style = MaterialTheme.typography.labelMedium,
                textAlign = TextAlign.End
            )
        }
        Slider(value = value, onValueChange = onValue, valueRange = 0f..1f)
    }
}
