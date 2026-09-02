package com.example.eso1

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import com.example.eso1.ui.screens.AscensionScreen
import com.example.eso1.ui.screens.HomeScreen
import com.example.eso1.ui.screens.MannequinScreen
import com.example.eso1.ui.screens.VibrantScreen
import com.example.eso1.ui.theme.Eso1Theme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            Eso1Theme(dynamicColor = false) {
                EsoApp()
            }
        }
    }
}

private enum class EsoDestination {
    Home,
    Vibrant,
    Mannequin,
    Ascension
}

@Composable
private fun EsoApp() {
    var destination by remember { mutableStateOf(EsoDestination.Home) }

    BackHandler(enabled = destination != EsoDestination.Home) {
        destination = EsoDestination.Home
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = Color(0xFF050509)
    ) {
        when (destination) {
            EsoDestination.Home -> HomeScreen(
                onOpenVibrant = { destination = EsoDestination.Vibrant },
                onOpenMannequin = { destination = EsoDestination.Mannequin },
                onOpenAscension = { destination = EsoDestination.Ascension }
            )

            EsoDestination.Vibrant -> VibrantScreen(
                onBack = { destination = EsoDestination.Home }
            )

            EsoDestination.Mannequin -> MannequinScreen(
                onBack = { destination = EsoDestination.Home }
            )

            EsoDestination.Ascension -> AscensionScreen(
                onBack = { destination = EsoDestination.Home }
            )
        }
    }
}
