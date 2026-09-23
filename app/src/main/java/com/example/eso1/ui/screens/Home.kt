package com.example.eso1.ui.screens

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.cos
import kotlin.math.sin

private data class Experience(
    val title: String,
    val subtitle: String,
    val accent: Color,
    val active: Boolean,
    val onClick: () -> Unit
)

@Composable
fun HomeScreen(
    onOpenVibrant: () -> Unit,
    onOpenMannequin: () -> Unit,
    onOpenAscension: () -> Unit
) {
    val experiences = listOf(
        Experience("Vibrant", "Room frequency cleanser", Color(0xFF22D3EE), true, onOpenVibrant),
        Experience("Mannequin", "Body map and chakra prompts", Color(0xFFFF4FA3), true, onOpenMannequin),
        Experience("Ascension", "Camera ritual to send a ghost to light", Color(0xFFFFD166), true, onOpenAscension),
        Experience("Aura Scanner", "Color field reflection", Color(0xFF8B5CF6), false) {},
        Experience("Focus Tunnel", "Attention narrowing loop", Color(0xFF34D399), false) {},
        Experience("Dream Chamber", "Night prompt generator", Color(0xFF60A5FA), false) {},
        Experience("Energy Dial", "One-control state shift", Color(0xFFF97316), false) {}
    )

    val transition = rememberInfiniteTransition(label = "home")
    val drift by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(12000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "drift"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF050509))
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            drawRect(
                brush = Brush.radialGradient(
                    colors = listOf(Color(0x3322D3EE), Color.Transparent),
                    center = Offset(size.width * (0.25f + drift * 0.35f), size.height * 0.2f),
                    radius = size.minDimension * 0.8f
                )
            )
            drawRect(
                brush = Brush.radialGradient(
                    colors = listOf(Color(0x26FF4FA3), Color.Transparent),
                    center = Offset(size.width * 0.85f, size.height * (0.8f - drift * 0.25f)),
                    radius = size.minDimension * 0.7f
                )
            )
            repeat(9) { index ->
                val angle = drift * 6.28318f + index * 0.7f
                drawCircle(
                    color = Color.White.copy(alpha = 0.025f),
                    radius = 90.dp.toPx() + index * 17.dp.toPx(),
                    center = Offset(
                        x = size.width * 0.5f + cos(angle) * 30.dp.toPx(),
                        y = size.height * 0.35f + sin(angle) * 18.dp.toPx()
                    ),
                    style = Stroke(width = 1.dp.toPx())
                )
            }
        }

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 20.dp, top = 68.dp, end = 20.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                Text(
                    text = "Eso1",
                    color = Color.White,
                    style = MaterialTheme.typography.displaySmall,
                    fontWeight = FontWeight.Black,
                    letterSpacing = 0.sp
                )
                Text(
                    text = "Strange tools for shifting the room.",
                    color = Color(0xFFB7BBC8),
                    style = MaterialTheme.typography.bodyLarge
                )
                Spacer(modifier = Modifier.height(24.dp))
            }

            items(experiences) { experience ->
                ExperienceCard(experience = experience)
            }
        }
    }
}

@Composable
private fun ExperienceCard(experience: Experience) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .height(106.dp)
            .clickable(enabled = experience.active, onClick = experience.onClick),
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xCC11131B))
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 18.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Canvas(
                modifier = Modifier
                    .height(54.dp)
                    .weight(0.2f)
            ) {
                val center = Offset(size.width / 2f, size.height / 2f)
                drawCircle(
                    color = experience.accent.copy(alpha = if (experience.active) 0.28f else 0.08f),
                    radius = size.minDimension * 0.45f,
                    center = center
                )
                drawCircle(
                    color = experience.accent.copy(alpha = if (experience.active) 0.9f else 0.28f),
                    radius = size.minDimension * 0.24f,
                    center = center,
                    style = Stroke(width = 2.dp.toPx())
                )
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = experience.title,
                    color = if (experience.active) Color.White else Color(0xFF727786),
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = experience.subtitle,
                    color = if (experience.active) Color(0xFFB7BBC8) else Color(0xFF565B66),
                    style = MaterialTheme.typography.bodyMedium
                )
            }
            Text(
                text = if (experience.active) "Open" else "Later",
                color = if (experience.active) experience.accent else Color(0xFF555B66),
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold
            )
        }
    }
}
