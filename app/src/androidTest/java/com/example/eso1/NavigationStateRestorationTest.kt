package com.example.eso1

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import androidx.test.ext.junit.runners.AndroidJUnit4

/**
 * Verifies the selected destination survives activity recreation
 * (e.g. activity recreation after a configuration change) instead of
 * resetting to Home.
 */
@RunWith(AndroidJUnit4::class)
class NavigationStateRestorationTest {

    @get:Rule
    val composeTestRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun destinationSurvivesActivityRecreation() {
        composeTestRule
            .onNodeWithContentDescription("Vibrant. Room frequency cleanser")
            .performClick()

        composeTestRule.onNodeWithText("Vibrant").assertIsDisplayed()

        composeTestRule.activityRule.scenario.recreate()

        composeTestRule.onNodeWithText("Vibrant").assertIsDisplayed()
        composeTestRule.onNodeWithText("Back").assertIsDisplayed()
        composeTestRule.onNodeWithText("Eso1").assertDoesNotExist()
    }
}
