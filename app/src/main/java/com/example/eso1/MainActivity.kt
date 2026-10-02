package com.example.eso1

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedContentTransitionScope.SlideDirection
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
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
        // App theme is dark-only; force light system-bar icons instead of
        // letting enableEdgeToEdge() derive icon appearance from system night mode.
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
            navigationBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT)
        )
        setContent {
            Eso1Theme {
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

    fun navigateTo(next: EsoDestination) {
        destination = next
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = Color(0xFF050509)
    ) {
        AnimatedContent(
            targetState = destination,
            label = "destination",
            transitionSpec = {
                val enteringHome = targetState == EsoDestination.Home
                val slideDirection = if (enteringHome) SlideDirection.End else SlideDirection.Start
                (slideIntoContainer(
                    towards = slideDirection,
                    animationSpec = tween(320)
                ) + fadeIn(tween(320))) togetherWith
                    (slideOutOfContainer(
                        towards = slideDirection,
                        animationSpec = tween(320)
                    ) + fadeOut(tween(220)))
            }
        ) { current ->
            when (current) {
                EsoDestination.Home -> HomeScreen(
                    onOpenVibrant = { navigateTo(EsoDestination.Vibrant) },
                    onOpenMannequin = { navigateTo(EsoDestination.Mannequin) },
                    onOpenAscension = { navigateTo(EsoDestination.Ascension) }
                )

                EsoDestination.Vibrant -> VibrantScreen(
                    onBack = { navigateTo(EsoDestination.Home) }
                )

                EsoDestination.Mannequin -> MannequinScreen(
                    onBack = { navigateTo(EsoDestination.Home) }
                )

                EsoDestination.Ascension -> AscensionScreen(
                    onBack = { navigateTo(EsoDestination.Home) }
                )
            }
        }
    }
}
