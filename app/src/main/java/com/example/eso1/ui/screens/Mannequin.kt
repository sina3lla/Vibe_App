package com.example.eso1.ui.screens

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import kotlin.math.sin

private enum class MannequinStyle(val label: String, val accent: Color) {
    Glass("Glass", Color(0xFF67E8F9)),
    Ember("Ember", Color(0xFFFF6B6B)),
    Violet("Violet", Color(0xFFA78BFA))
}

private data class BodyZone(
    val title: String,
    val body: String
)

@Composable
fun MannequinScreen(onBack: () -> Unit) {
    var style by remember { mutableStateOf(MannequinStyle.Glass) }
    var selectedZone by remember { mutableStateOf<BodyZone?>(null) }
    val transition = rememberInfiniteTransition(label = "mannequin")
    val breath by transition.animateFloat(
        initialValue = -1f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(2600),
            repeatMode = RepeatMode.Reverse
        ),
        label = "breath"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF07060C))
            .padding(horizontal = 18.dp, vertical = 34.dp)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            drawRect(
                brush = Brush.verticalGradient(
                    colors = listOf(Color(0xFF07060C), style.accent.copy(alpha = 0.12f), Color(0xFF07060C))
                )
            )
        }

        Column(modifier = Modifier.fillMaxSize()) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TextButton(onClick = onBack) {
                    Text("Back")
                }
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    text = "Mannequin",
                    color = Color.White,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.weight(1f))
                Spacer(modifier = Modifier.width(62.dp))
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally)
            ) {
                MannequinStyle.entries.forEach { option ->
                    FilterChip(
                        selected = style == option,
                        onClick = { style = option },
                        label = { Text(option.label) }
                    )
                }
            }

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(vertical = 24.dp),
                contentAlignment = Alignment.Center
            ) {
                MannequinFigure(
                    style = style,
                    breath = breath,
                    onZone = { selectedZone = it }
                )
            }

            Text(
                text = "Touch the head, chest, belly, hands, or legs.",
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xA60F1118), RoundedCornerShape(8.dp))
                    .padding(16.dp),
                color = Color(0xFFD6DAE3),
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }

    selectedZone?.let { zone ->
        AlertDialog(
            onDismissRequest = { selectedZone = null },
            confirmButton = {
                TextButton(onClick = { selectedZone = null }) {
                    Text("Close")
                }
            },
            title = { Text(zone.title) },
            text = { Text(zone.body) },
            containerColor = Color(0xFF11131B),
            titleContentColor = Color.White,
            textContentColor = Color(0xFFD6DAE3)
        )
    }
}

@Composable
private fun MannequinFigure(
    style: MannequinStyle,
    breath: Float,
    onZone: (BodyZone) -> Unit
) {
    Canvas(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(style) {
                detectTapGestures { tap ->
                    locateBodyZone(tap, size)?.let(onZone)
                }
            }
    ) {
        val centerX = size.width / 2f
        val baseY = size.height * 0.11f + breath * 6.dp.toPx()
        val head = Offset(centerX, baseY + size.height * 0.1f)
        val neckY = baseY + size.height * 0.19f
        val chestY = baseY + size.height * 0.31f
        val hipY = baseY + size.height * 0.53f
        val footY = baseY + size.height * 0.86f
        val glow = style.accent.copy(alpha = 0.26f)

        drawCircle(style.accent.copy(alpha = 0.16f), radius = size.minDimension * 0.36f, center = Offset(centerX, chestY))
        drawCircle(style.accent.copy(alpha = 0.08f), radius = size.minDimension * 0.52f, center = Offset(centerX, chestY))

        drawCircle(
            color = glow,
            radius = size.minDimension * 0.095f,
            center = head
        )
        drawCircle(
            color = Color.White.copy(alpha = 0.86f),
            radius = size.minDimension * 0.075f,
            center = head,
            style = Stroke(width = 2.dp.toPx())
        )

        val bodyPath = Path().apply {
            moveTo(centerX, neckY)
            cubicTo(centerX - 78.dp.toPx(), chestY, centerX - 52.dp.toPx(), hipY, centerX - 20.dp.toPx(), hipY)
            lineTo(centerX + 20.dp.toPx(), hipY)
            cubicTo(centerX + 52.dp.toPx(), hipY, centerX + 78.dp.toPx(), chestY, centerX, neckY)
            close()
        }
        drawPath(
            path = bodyPath,
            brush = Brush.verticalGradient(
                listOf(Color.White.copy(alpha = 0.2f), style.accent.copy(alpha = 0.08f))
            )
        )
        drawPath(
            path = bodyPath,
            color = Color.White.copy(alpha = 0.72f),
            style = Stroke(width = 2.dp.toPx())
        )

        drawLine(
            color = style.accent.copy(alpha = 0.72f),
            start = Offset(centerX - 47.dp.toPx(), chestY + 4.dp.toPx()),
            end = Offset(centerX - 120.dp.toPx(), hipY - 10.dp.toPx() + sin(breath) * 7.dp.toPx()),
            strokeWidth = 12.dp.toPx(),
            cap = StrokeCap.Round
        )
        drawLine(
            color = style.accent.copy(alpha = 0.72f),
            start = Offset(centerX + 47.dp.toPx(), chestY + 4.dp.toPx()),
            end = Offset(centerX + 120.dp.toPx(), hipY - 10.dp.toPx() - sin(breath) * 7.dp.toPx()),
            strokeWidth = 12.dp.toPx(),
            cap = StrokeCap.Round
        )
        drawLine(
            color = Color.White.copy(alpha = 0.7f),
            start = Offset(centerX - 16.dp.toPx(), hipY),
            end = Offset(centerX - 54.dp.toPx(), footY),
            strokeWidth = 14.dp.toPx(),
            cap = StrokeCap.Round
        )
        drawLine(
            color = Color.White.copy(alpha = 0.7f),
            start = Offset(centerX + 16.dp.toPx(), hipY),
            end = Offset(centerX + 54.dp.toPx(), footY),
            strokeWidth = 14.dp.toPx(),
            cap = StrokeCap.Round
        )

        listOf(chestY - 42.dp.toPx(), chestY, hipY - 52.dp.toPx(), hipY - 2.dp.toPx()).forEachIndexed { index, y ->
            drawCircle(
                color = style.accent.copy(alpha = 0.32f + index * 0.08f),
                radius = 9.dp.toPx() + breath * 1.4.dp.toPx(),
                center = Offset(centerX, y)
            )
        }
    }
}

private fun locateBodyZone(tap: Offset, size: IntSize): BodyZone? {
    val centerX = size.width / 2f
    val baseY = size.height * 0.11f
    val headRect = Rect(centerX - 58f, baseY + size.height * 0.02f, centerX + 58f, baseY + size.height * 0.2f)
    val chestRect = Rect(centerX - 96f, baseY + size.height * 0.22f, centerX + 96f, baseY + size.height * 0.42f)
    val bellyRect = Rect(centerX - 80f, baseY + size.height * 0.42f, centerX + 80f, baseY + size.height * 0.62f)
    val handsRect = Rect(centerX - 170f, baseY + size.height * 0.28f, centerX + 170f, baseY + size.height * 0.6f)
    val legsRect = Rect(centerX - 90f, baseY + size.height * 0.6f, centerX + 90f, baseY + size.height * 0.95f)

    return when {
        headRect.contains(tap) -> BodyZone(
            title = "Crown / Brow",
            body = "This point is used as an attention anchor. In chakra language it belongs to intuition, memory, dreams, and the pressure of thought. Hold your gaze here when you want the app to feel quiet and vertical."
        )

        chestRect.contains(tap) -> BodyZone(
            title = "Heart Field",
            body = "The chest marker is the emotional center of the ritual body. Treat it as a symbolic place for grief, warmth, attachment, and release. Slow breathing makes this zone feel heavier and more believable."
        )

        bellyRect.contains(tap) -> BodyZone(
            title = "Solar / Root",
            body = "The lower center is for will, hunger, fear, and grounding. When this area pulses, imagine the mannequin becoming heavier, more present, and less scattered."
        )

        handsRect.contains(tap) -> BodyZone(
            title = "Hands",
            body = "Hands represent action and contact. In this interface they are the parts that carry intent outward, like the place where a ritual becomes a gesture."
        )

        legsRect.contains(tap) -> BodyZone(
            title = "Legs",
            body = "The legs are the anchor points. They suggest territory, boundaries, and the decision to stay in the room instead of drifting away from it."
        )

        else -> null
    }
}
