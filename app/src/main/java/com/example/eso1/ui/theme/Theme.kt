package com.example.eso1.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/**
 * Every screen in the app paints its own dark ritual backdrop directly (hardcoded canvas
 * gradients, black surfaces). The app is dark-only by design, not by system setting: letting
 * [MaterialTheme] drift to a light scheme (e.g. via system settings) would mismatch default
 * component chrome (sliders, chips, dialogs) against the permanently dark screens.
 */
private val Eso1ColorScheme = darkColorScheme(
    primary = Cyan80,
    secondary = Violet80,
    tertiary = Gold80,
    background = Color(0xFF050509),
    surface = Color(0xFF0E1118),
    onBackground = Color(0xFFE5E7EB),
    onSurface = Color(0xFFE5E7EB)
)

@Composable
fun Eso1Theme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = Eso1ColorScheme,
        typography = Typography,
        content = content
    )
}
