package com.example.eso1.ui.engine

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.example.eso1.ui.theme.Eso1Theme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import androidx.test.ext.junit.runners.AndroidJUnit4

/**
 * Covers CURRENT_TASK's two required assertions: the harness survives first
 * composition, and its non-spatial fallback is reachable without depending on
 * whatever the native Filament surface actually does on this device.
 */
@RunWith(AndroidJUnit4::class)
class EngineHarnessTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun firstCompositionDoesNotCrashAndExposesEngineCanvas() {
        composeTestRule.setContent {
            Eso1Theme {
                EngineHarness()
            }
        }

        composeTestRule.onNodeWithTag("engine-canvas").assertIsDisplayed()
    }

    @Test
    fun nonSpatialFallbackIsReachableWithoutTheRenderedSurface() {
        composeTestRule.setContent {
            Eso1Theme {
                EngineHarness()
            }
        }

        // Whether the native Filament surface actually comes up on this device is not
        // something this test should assume either way: if it did, switch to the fallback
        // explicitly; if it didn't, the harness already fell back on its own.
        val toggle = composeTestRule.onAllNodesWithText("Switch to text description")
        if (toggle.fetchSemanticsNodes().isNotEmpty()) {
            toggle[0].performClick()
        }

        composeTestRule.onNodeWithTag("engine-canvas").assertIsDisplayed()
        composeTestRule
            .onNodeWithText("Non-spatial description", substring = true)
            .assertIsDisplayed()
    }
}
