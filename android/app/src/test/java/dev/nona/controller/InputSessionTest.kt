package dev.nona.controller

import org.junit.Assert.*
import org.junit.Test

class InputSessionTest {
    class Sink : ReportSink {
        override var ready = true
        val reports = mutableListOf<Pair<Int,ByteArray>>()
        override fun send(id:Int,report:ByteArray):Boolean{if(!ready)return false;reports.add(id to report.copyOf());return true}
    }
    @Test fun keyboardEncodingSupportsChordsAndModifiers(){
        assertArrayEquals(byteArrayOf(2,0,4,7,0x1a,0x2c,0,0),HidReports.keyboard(setOf(0x1a,7,4,0x2c),2))
        assertArrayEquals(byteArrayOf(2,-10,20,0),HidReports.mouse(-10,20,true))
    }
    @Test(expected=IllegalArgumentException::class) fun oversizedKeyboardRejected(){HidReports.keyboard((4..10).toSet())}
    @Test(expected=IllegalArgumentException::class) fun outOfRangePointerRejected(){HidReports.mouse(128)}
    @Test fun getReportStateNeverReplaysRelativeMouseMovement(){
        assertArrayEquals(byteArrayOf(2,0,0,0),HidReports.mouseState(HidReports.mouse(70,-50,true)))
    }
    @Test fun noInputBeforeStartAndNoAutomaticResume(){
        val sink=Sink();val input=InputSession(sink)
        input.move(1f,-1f);input.action("a",true);input.flush();assertTrue(sink.reports.isEmpty())
        sink.ready=false;assertFalse(input.start());sink.ready=true;input.flush();assertFalse(input.active)
        assertTrue(input.start());input.flush();assertTrue(sink.reports.last().second.all{it.toInt()==0})
    }
    @Test fun simultaneousMovementLookJumpAndStop(){
        val sink=Sink();val input=InputSession(sink);input.start();sink.reports.clear()
        input.move(.7f,-.7f);input.look(true);input.camera(12f,-9f);input.action("a",true)
        val keyboard=sink.reports.last{it.first==1}.second
        assertTrue(keyboard.contains(7));assertTrue(keyboard.contains(0x1a));assertTrue(keyboard.contains(0x2c))
        assertArrayEquals(byteArrayOf(2,12,-9,0),sink.reports.last{it.first==2}.second)
        val count=sink.reports.size;input.flush();assertEquals(count,sink.reports.size)
        input.pause();assertFalse(input.active)
        assertTrue(sink.reports.takeLast(2).all{it.second.all{b->b.toInt()==0}})
    }
    @Test fun pointerRequiresClutchAndCannotQueueUnboundedMovement(){
        val sink=Sink();val input=InputSession(sink);input.start();sink.reports.clear()
        input.camera(100f,50f);input.flush();assertTrue(sink.reports.isEmpty())
        input.look(true);repeat(100){input.camera(50f,-50f)};input.flush()
        assertArrayEquals(byteArrayOf(2,127,-127,0),sink.reports.last().second)
        input.look(false);assertArrayEquals(HidReports.mouse(),sink.reports.last().second)
    }
    @Test fun profileAndConnectionChangesReturnToNeutral(){
        val sink=Sink();var failures=0;val input=InputSession(sink){failures++};input.start()
        input.move(1f,0f);input.flush();input.profile=ControlProfile.RACING;assertFalse(input.active)
        input.start();sink.ready=false;input.flush();assertFalse(input.active);assertEquals(1,failures)
        sink.ready=true;input.flush();assertFalse(input.active)
    }
    @Test fun shortTapProducesPressAndReleaseWithoutWaitingForTick(){
        val sink=Sink();val input=InputSession(sink);input.start();sink.reports.clear()
        input.action("a",true);input.action("a",false)
        assertTrue(sink.reports[0].second.contains(0x2c));assertArrayEquals(HidReports.keyboard(),sink.reports[1].second)
    }
    @Test fun gyroUsesNativeScreenAxesAndRejectsGaps(){
        val first=MotionMath.gyro(0f,1f,0,.02f)
        val landscape=MotionMath.gyro(-1f,0f,1,.02f)
        assertEquals(first.first,landscape.first,.0001f);assertEquals(0f,first.second,.0001f)
        assertEquals(0f to 0f,MotionMath.gyro(1f,2f,0,1f))
        assertEquals(0f to 0f,MotionMath.gyro(Float.NaN,1f,0,.02f))
    }
    @Test fun hidDescriptorDeclaresReportLengthsUsedByWindows(){
        var i=0;var size=0;var count=0;var id=0
        val input=mutableMapOf<Int,Int>();val output=mutableMapOf<Int,Int>()
        while(i<HidReports.descriptor.size){
            val prefix=HidReports.descriptor[i++].toInt()and 255
            val length=when(prefix and 3){3->4;else->prefix and 3}
            var value=0;repeat(length){shift->value=value or ((HidReports.descriptor[i++].toInt()and 255)shl(shift*8))}
            when(prefix and 0xfc){0x74->size=value;0x94->count=value;0x84->id=value
                0x80->input[id]=(input[id]?:0)+size*count
                0x90->output[id]=(output[id]?:0)+size*count}
        }
        assertEquals(mapOf(1 to 64,2 to 32),input);assertEquals(mapOf(1 to 8),output)
    }

    @Test fun eightWaySectorsKeepStraightAheadClean(){
        fun at(degrees:Double,length:Float=1f)=StickMath.eightWay(
            (kotlin.math.cos(Math.toRadians(degrees))*length).toFloat(),(kotlin.math.sin(Math.toRadians(degrees))*length).toFloat())
        // Screen y grows downward, so -90° is forward (W).
        assertEquals(0 to -1,at(-90.0+20))   // 20° thumb drift: per-axis thresholds used to add strafe here
        assertEquals(1 to -1,at(-45.0))
        assertEquals(1 to 0,at(0.0))
        assertEquals(0 to -1,at(-90.0+20,.5f)) // same answer at half deflection
        assertEquals(0 to 0,at(-90.0,.2f))
        // Hysteresis: once moving forward, a 28° wobble does not flicker into a diagonal.
        val drift=StickMath.eightWay(kotlin.math.cos(Math.toRadians(-62.0)).toFloat(),kotlin.math.sin(Math.toRadians(-62.0)).toFloat(),0,-1)
        assertEquals(0 to -1,drift)
        assertEquals(0 to -1,StickMath.eightWay(0f,-.15f,0,-1))
        assertEquals(0 to 0,StickMath.eightWay(Float.NaN,0f))
    }
    @Test fun pulsedSteeringIsProportionalAndFullLockHolds(){
        var now=0L;val sink=Sink();val input=InputSession(sink,{now})
        input.profile=ControlProfile.RACING;input.start()
        fun rightHeldMs(x:Float):Int{
            input.move(x,0f);var held=0
            repeat(100){input.flush();if(sink.reports.last{it.first==1}.second.contains(0x4F))held+=10;now+=10}
            return held/10
        }
        val half=rightHeldMs(.5f);val full=rightHeldMs(1f)
        assertTrue("half lock should hold right 50-70% of the time, was $half%",half in 50..70)
        assertEquals(100,full)
        input.move(0f,0f);input.flush();assertFalse(sink.reports.last{it.first==1}.second.contains(0x4F))
        // A new press is immediately "on", so steering response never waits for the next pulse.
        input.move(-.2f,0f);input.flush();assertTrue(sink.reports.last{it.first==1}.second.contains(0x50))
        input.pulsedSteering=false;input.move(.3f,0f);now+=95;input.flush()
        assertTrue(sink.reports.last{it.first==1}.second.contains(0x4F))
        assertEquals(0f,StickMath.steerDuty(.1f),0f);assertEquals(1f,StickMath.steerDuty(.95f),0f)
    }
}
