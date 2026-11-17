package dev.nona.controller

import android.content.Context
import android.graphics.*
import android.view.MotionEvent
import android.view.View
import kotlin.math.*

class ControllerSurface(context: Context, private val session: InputSession, private val cancelled: () -> Unit = {}) : View(context) {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val roles = mutableMapOf<Int, String>()
    private val points = mutableMapOf<Int, PointF>()
    private var origin: PointF? = null
    private var thumb: PointF? = null
    private val actions = linkedMapOf<String, RectF>()
    private val moveArea = RectF()
    private val lookArea = RectF()
    var lookHeld = false; private set
    private val density = resources.displayMetrics.density
    private val ink = Color.rgb(236, 235, 231)
    private val muted = Color.rgb(141, 147, 145)
    private val press = Color.rgb(255, 107, 44)      // the only bright colour: "you are pressing this"
    private val pressInk = Color.rgb(26, 12, 4)
    private val surface = Color.rgb(25, 28, 31)
    private val raised = Color.rgb(32, 36, 40)
    private val line = Color.rgb(44, 49, 54)

    init { id = R.id.controller_surface; isFocusable = true; contentDescription = "Movement surface, camera surface, and action buttons" }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        val gap = 14 * density
        moveArea.set(gap, gap, w * .44f, h - gap)
        lookArea.set(w * .51f, gap, w - gap, h - gap)
        val r = min(h * .135f, 34 * density).coerceAtLeast(18 * density)
        fun button(key: String, x: Float, y: Float) { actions[key] = RectF(x-r,y-r,x+r,y+r) }
        button("a", w*.88f, h*.77f); button("b",w*.72f,h*.83f)
        button("x",w*.89f,h*.31f); button("y",w*.72f,h*.40f)
    }

    private fun box(canvas: Canvas, rect: RectF) {
        paint.color = surface; paint.style = Paint.Style.FILL
        canvas.drawRoundRect(rect, 12*density, 12*density, paint)
        paint.color = line; paint.style = Paint.Style.STROKE; paint.strokeWidth = density
        canvas.drawRoundRect(rect, 12*density, 12*density, paint); paint.style = Paint.Style.FILL
    }

    private fun text(canvas: Canvas, value: String, x: Float, y: Float, size: Float, color: Int = muted) {
        paint.color=color; paint.textSize=size*density; paint.typeface=Typeface.create("sans-serif-medium",Typeface.NORMAL)
        paint.textAlign=Paint.Align.CENTER; canvas.drawText(value,x,y,paint)
    }

    override fun onDraw(canvas: Canvas) {
        val racing=session.profile==ControlProfile.RACING
        canvas.drawColor(Color.rgb(15, 17, 19)); box(canvas,moveArea)
        if(!racing)box(canvas,lookArea)
        val centre = origin ?: PointF(moveArea.centerX(),moveArea.centerY())
        val radius = min(moveArea.width(),moveArea.height())*.26f
        paint.style=Paint.Style.STROKE;paint.strokeWidth=density;paint.color=line
        canvas.drawCircle(centre.x,centre.y,radius,paint)
        // Thumb: a quiet ring at rest, solid while held.
        val handle=thumb?:centre
        paint.strokeWidth=2*density;paint.color=if(thumb!=null)ink else muted
        if(thumb!=null){paint.style=Paint.Style.FILL;paint.color=raised;canvas.drawCircle(handle.x,handle.y,22*density,paint);paint.style=Paint.Style.STROKE;paint.color=ink}
        canvas.drawCircle(handle.x,handle.y,22*density,paint);paint.style=Paint.Style.FILL
        text(canvas,if(racing)"Steer" else "Touch anywhere, drag to move",moveArea.centerX(),moveArea.bottom-16*density,12f)
        if(!racing)text(canvas,"Swipe to look",lookArea.centerX(),lookArea.bottom-16*density,12f,if(lookHeld)ink else muted)
        for((key,rect) in actions){
            val pressed=roles.values.contains(key)
            paint.style=Paint.Style.FILL;paint.color=if(pressed)press else raised
            canvas.drawCircle(rect.centerX(),rect.centerY(),rect.width()/2,paint)
            if(!pressed){paint.style=Paint.Style.STROKE;paint.strokeWidth=density;paint.color=line
                canvas.drawCircle(rect.centerX(),rect.centerY(),rect.width()/2,paint);paint.style=Paint.Style.FILL}
            val label=if(racing) mapOf("a" to "Gas","b" to "Brake","x" to "Slide","y" to "Boost")[key]
                else mapOf("a" to "Jump","b" to "Run","x" to "Use","y" to "Action")[key]
            text(canvas,label.orEmpty(),rect.centerX(),rect.centerY()+4*density,13f,if(pressed)pressInk else ink)
        }
        if(!session.active){
            paint.color=Color.argb(185,15,17,19);canvas.drawRect(0f,0f,width.toFloat(),height.toFloat(),paint)
            text(canvas,"Paused",width/2f,height/2f-6*density,18f,ink)
            text(canvas,"Focus your game on the PC, then tap Play",width/2f,height/2f+16*density,13f,muted)
        }
    }

    fun reset() {
        roles.clear();points.clear();origin=null;thumb=null;lookHeld=false;invalidate()
    }

    override fun performClick(): Boolean { super.performClick(); return true }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if(!session.active)return true
        when(event.actionMasked){
            MotionEvent.ACTION_DOWN,MotionEvent.ACTION_POINTER_DOWN->{
                val i=event.actionIndex;val id=event.getPointerId(i);val p=PointF(event.getX(i),event.getY(i))
                val button=actions.entries.firstOrNull { it.value.contains(p.x,p.y) }?.key
                val role=button?:if(moveArea.contains(p.x,p.y)&&!roles.containsValue("move"))"move"
                    else if(lookArea.contains(p.x,p.y)&&!roles.containsValue("look")&&session.profile==ControlProfile.MOVE_LOOK)"look" else "none"
                roles[id]=role;points[id]=p
                when(role){
                    "move"->{origin=PointF(p.x,p.y);thumb=PointF(p.x,p.y);session.move(0f,0f)}
                    "look"->{lookHeld=true;session.look(true)}
                    "a","b","x","y"->session.action(role,true)
                }
            }
            MotionEvent.ACTION_MOVE->{
                for(i in 0 until event.pointerCount){
                    val id=event.getPointerId(i);val x=event.getX(i);val y=event.getY(i)
                    when(roles[id]){
                        "move"->{
                            val start=origin?:continue;val radius=min(moveArea.width(),moveArea.height())*.28f
                            var dx=(x-start.x)/radius;var dy=(y-start.y)/radius;val length=hypot(dx,dy)
                            if(length<=.08f){dx=0f;dy=0f}else{val gain=((length-.08f)/.92f).coerceAtMost(1f)/length;dx*=gain;dy*=gain}
                            session.move(dx,dy);thumb=PointF(start.x+dx*radius*.6f,start.y+dy*radius*.6f)
                        }
                        "look"->{val previous=points[id]?:continue;session.camera((x-previous.x)/density,(y-previous.y)/density)}
                    }
                    points[id]=PointF(x,y)
                }
            }
            MotionEvent.ACTION_UP,MotionEvent.ACTION_POINTER_UP->{
                val id=event.getPointerId(event.actionIndex);val role=roles.remove(id);points.remove(id)
                when(role){
                    "move"->{origin=null;thumb=null;session.move(0f,0f);session.flush()}
                    "look"->{lookHeld=false;session.look(false)}
                    "a","b","x","y"->if(!roles.containsValue(role))session.action(role,false)
                }
                if(event.actionMasked==MotionEvent.ACTION_UP)performClick()
            }
            MotionEvent.ACTION_CANCEL->{session.pause();reset();cancelled()}
        }
        invalidate();return true
    }
}
