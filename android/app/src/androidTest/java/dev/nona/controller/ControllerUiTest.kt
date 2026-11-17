package dev.nona.controller

import android.content.Intent
import android.graphics.Bitmap
import android.view.MotionEvent
import androidx.lifecycle.Lifecycle
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.*
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.Before
import org.junit.After
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class ControllerUiTest {
    @Before fun usePreview(){LinkFactory.previewForTests=true}
    @After fun clearPreview(){LinkFactory.previewForTests=false}
    private fun screenshot(name:String){
        val instrumentation=InstrumentationRegistry.getInstrumentation()
        val folder=File(instrumentation.targetContext.getExternalFilesDir(null),"ui").apply{mkdirs()}
        val bitmap=instrumentation.uiAutomation.takeScreenshot()
        try { File(folder,"$name.png").outputStream().use{bitmap.compress(Bitmap.CompressFormat.PNG,100,it)} }
        finally { bitmap.recycle() }
    }
    @Test fun nativePairPlayStopAndBackgroundAreNeutral(){
        val intent=Intent(ApplicationProvider.getApplicationContext(),MainActivity::class.java)
        ActivityScenario.launch<MainActivity>(intent).use{scenario->
            onView(withId(R.id.link_status)).check(matches(withText("Choose a paired computer, or pair a new one.")))
            screenshot("android-pairing")
            onView(withContentDescription("Connect to Windows laptop")).perform(click())
            onView(withId(R.id.open_controller)).check(matches(isDisplayed())).perform(click())
            onView(withId(R.id.play_stop)).check(matches(withText("Play"))).perform(click())
            onView(withId(R.id.play_stop)).check(matches(withText("Stop")))
            scenario.onActivity{activity->
                val view=activity.findViewById<ControllerSurface>(R.id.controller_surface)
                val now=android.os.SystemClock.uptimeMillis()
                fun touch(action:Int,x:Float,y:Float,time:Long){val event=MotionEvent.obtain(now,time,action,x,y,0);view.dispatchTouchEvent(event);event.recycle()}
                touch(MotionEvent.ACTION_DOWN,view.width*.22f,view.height*.5f,now)
                touch(MotionEvent.ACTION_MOVE,view.width*.32f,view.height*.4f,now+20)
                activity.session.flush()
                val link=activity.link as PreviewLink
                assertTrue(link.reports.any{it.first==1&&it.second.any{b->b.toInt()!=0}})
                touch(MotionEvent.ACTION_UP,view.width*.32f,view.height*.4f,now+40)
                assertTrue(link.reports.last{it.first==1}.second.all{it.toInt()==0})
                val stop=activity.findViewById<android.widget.Button>(R.id.play_stop)
                assertTrue(stop.bottom<=activity.window.decorView.height)
            }
            screenshot("android-controller")
            onView(withId(R.id.play_stop)).perform(click()).check(matches(withText("Play")))
            scenario.onActivity{activity->
                activity.session.start();activity.session.move(1f,0f);activity.session.look(true);activity.session.flush()
            }
            scenario.moveToState(Lifecycle.State.CREATED)
            scenario.onActivity{activity->
                assertFalse(activity.session.active)
                assertEquals(0,activity.window.attributes.flags and android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                val reports=(activity.link as PreviewLink).reports
                assertTrue(reports.takeLast(2).all{it.second.all{byte->byte.toInt()==0}})
            }
            scenario.moveToState(Lifecycle.State.RESUMED)
            scenario.onActivity{assertFalse(it.session.active)}
        }
    }
}
