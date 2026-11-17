package dev.nona.controller

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.bluetooth.BluetoothAdapter
import android.content.*
import android.content.pm.ActivityInfo
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.hardware.*
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.*

private const val IDLE_LINK_MS = 10 * 60 * 1000L

class MainActivity : Activity(), SensorEventListener {
    lateinit var link: ControllerLink; private set
    lateinit var session: InputSession; private set
    private lateinit var root: LinearLayout
    private var surface: ControllerSurface? = null
    private var inController = false
    private var foreground = false
    private var systemPrompt = false
    private var gyroEnabled = false
    private var invertGyro = false
    private var gyroTime = 0L
    private var lastGyro = 0L
    private val handler = Handler(Looper.getMainLooper())
    private val sensors by lazy { getSystemService(SensorManager::class.java) }
    private val gyro by lazy { sensors?.getDefaultSensor(Sensor.TYPE_GYROSCOPE) }
    private val preferences by lazy { getSharedPreferences("nona-controls", MODE_PRIVATE) }
    // One system with the web controller: graphite, white primary, colour only for state.
    private val bg = Color.rgb(15,17,19)
    private val raised = Color.rgb(32,36,40)
    private val line = Color.rgb(54,61,67)
    private val ink = Color.rgb(236,235,231)
    private val muted = Color.rgb(141,147,145)
    private val ok = Color.rgb(62,207,110)
    private val warn = Color.rgb(227,163,58)
    private val stopRed = Color.rgb(239,79,79)
    private val dark = bg
    private var hostsSignature = ""

    private fun dp(value: Int) = (value*resources.displayMetrics.density).toInt()
    private fun text(value: String, size: Float = 15f, color: Int = ink) = TextView(this).apply {
        text=value;textSize=size;setTextColor(color);setLineSpacing(dp(3).toFloat(),1f)
    }
    private fun shape(fill: Int, border: Int? = null) = GradientDrawable().apply {
        setColor(fill);cornerRadius=dp(8).toFloat();if(border!=null)setStroke(dp(1),border)
    }
    private fun button(value: String, primary: Boolean = false, action: () -> Unit) = Button(this).apply {
        text=value;isAllCaps=false;textSize=14f;typeface=Typeface.create("sans-serif-medium",Typeface.NORMAL)
        stateListAnimator=null;elevation=0f
        setTextColor(if(primary)bg else ink)
        background=if(primary)shape(ink) else shape(raised,line)
        minHeight=dp(48);setPadding(dp(16),dp(8),dp(16),dp(8));setOnClickListener{action()}
    }
    private fun LinearLayout.space(height: Int) { addView(View(this@MainActivity),LinearLayout.LayoutParams(1,dp(height))) }
    private fun LinearLayout.full(view: View) { addView(view,LinearLayout.LayoutParams(-1,-2)) }
    private fun allowed() = link.preview || Build.VERSION.SDK_INT<31 || checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)==PackageManager.PERMISSION_GRANTED

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        link=LinkFactory.create(this)
        session=InputSession(link) { pauseInput("Connection interrupted. Reconnect before playing.") }
        session.lookSpeed=preferences.getFloat("lookSpeed",1f)
        session.holdRight=preferences.getBoolean("holdRight",true)
        session.pulsedSteering=preferences.getBoolean("pulsedSteering",true)
        invertGyro=preferences.getBoolean("invertGyro",false)
        link.changed={ status ->
            keepLink(status)
            if(!status.ready)pauseInput(status.message)
            if(inController)updateController() else renderPairing()
        }
        renderPairing()
    }

    override fun onResume() {
        super.onResume();foreground=true;systemPrompt=false
        if(allowed())link.start()
        keepLink(link.status)
        handler.post(ticker)
    }
    override fun onPause() {
        pauseInput();foreground=false;handler.removeCallbacks(ticker)
        super.onPause()
    }
    override fun onStart() { super.onStart();handler.removeCallbacks(idleStop) }
    // Input is already neutral (onPause). The link itself survives a lock or a pairing screen,
    // so returning only needs Play. Ten idle minutes off-screen release the computer entirely.
    override fun onStop() { handler.removeCallbacks(idleStop);handler.postDelayed(idleStop,IDLE_LINK_MS);super.onStop() }
    override fun onDestroy() { handler.removeCallbacksAndMessages(null);link.stop();LinkService.stop(this);super.onDestroy() }
    private val idleStop=Runnable{ if(!systemPrompt){link.stop();LinkService.stop(this)} }
    private fun keepLink(status: LinkStatus) {
        if(link.preview)return
        if(status.registered){ if(foreground)LinkService.start(this) } else LinkService.stop(this)
    }
    override fun onConfigurationChanged(newConfig: Configuration) { super.onConfigurationChanged(newConfig);pauseInput();if(inController)renderController()else renderPairing() }

    private val ticker=object:Runnable {
        override fun run(){
            if(!foreground)return
            session.flush()
            if(gyroActive()&&session.active&&SystemClock.elapsedRealtime()-lastGyro>750){gyroEnabled=false;pauseInput("Motion readings stopped. Tap Play to continue with touch.")}
            if(session.active)surface?.invalidate()
            if(!inController){val signature=link.computers().joinToString{it.address};if(signature!=hostsSignature)renderPairing()}
            // 50 Hz. Keep this above ~15 ms: a faster repeating main-thread message never lets
            // the UI go idle (Espresso hangs on it) and costs battery for no visible gain.
            handler.postDelayed(this,if(inController)20 else 1500)
        }
    }

    private fun shell(color: Int): LinearLayout {
        window.statusBarColor=color;window.navigationBarColor=color
        window.decorView.systemUiVisibility=0
        root=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;setBackgroundColor(color) }
        root.setOnApplyWindowInsetsListener { view, insets ->
            if(Build.VERSION.SDK_INT>=30){val bars=insets.getInsets(WindowInsets.Type.systemBars());view.setPadding(bars.left,bars.top,bars.right,bars.bottom)}
            else view.setPadding(insets.systemWindowInsetLeft,insets.systemWindowInsetTop,insets.systemWindowInsetRight,insets.systemWindowInsetBottom)
            insets
        }
        setContentView(root);root.requestApplyInsets();return root
    }

    private fun statusColor()=when{
        link.ready->ok
        link.status.stage in setOf("permission","unsupported","error","disabled")->stopRed
        else->warn
    }
    private fun dot(color: Int)=View(this).apply{background=GradientDrawable().apply{shape=GradientDrawable.OVAL;setColor(color)}}

    private fun renderPairing() {
        if(inController)return
        val outer=shell(bg)
        val content=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;setPadding(dp(22),dp(18),dp(22),dp(24)) }
        val scroll=ScrollView(this);scroll.addView(content);outer.addView(scroll)
        val top=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL}
        top.addView(text("NONA",15f).apply{typeface=Typeface.create("sans-serif",Typeface.BOLD);letterSpacing=.04f},LinearLayout.LayoutParams(0,-2,1f))
        top.addView(text(if(link.preview)"UI preview · no Bluetooth output" else "${BuildConfig.VERSION_NAME}",12f,muted))
        content.full(top)
        content.space(36)
        content.full(text("Connect to your PC",24f).apply{typeface=Typeface.create("sans-serif-medium",Typeface.NORMAL)})
        content.space(6);content.full(text("Your phone acts as a Bluetooth keyboard and mouse. Nothing to install on the PC.",14f,muted))
        content.space(24)
        val state=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL}
        state.addView(dot(statusColor()),LinearLayout.LayoutParams(dp(8),dp(8)).apply{rightMargin=dp(10)})
        state.addView(text(link.status.message,14f).apply{id=R.id.link_status},LinearLayout.LayoutParams(0,-2,1f))
        content.full(state)
        content.space(14)
        if(!link.status.registered){
            val title=when{!allowed()->"Allow Bluetooth";link.status.stage=="disabled"->"Turn on Bluetooth";link.status.stage=="preparing"->"Retry Bluetooth setup";else->"Set up Bluetooth"}
            content.full(button(title,true){prepareBluetooth()}.apply{id=R.id.link_action})
        }else if(!link.ready){
            content.full(button("Pair a new computer"){pairNewComputer()}.apply{id=R.id.link_action})
        }
        if(link.ready){
            content.full(button("Open controller",true){openController()}.apply{id=R.id.open_controller})
        }
        content.space(30);content.full(text("Paired devices",13f,muted))
        content.space(8)
        val hosts=link.computers();hostsSignature=hosts.joinToString{it.address}
        val list=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;id=R.id.host_list}
        if(hosts.isEmpty())list.addView(text("On the PC: Settings → Bluetooth & devices → Add device → Bluetooth, then pick this phone. Tap \"Pair a new computer\" first so the PC can see it.",14f,muted))
        for(host in hosts){
            val connected=link.status.host?.address==host.address&&link.ready
            val enabled=link.status.registered&&link.status.stage!="connecting"
            val row=LinearLayout(this).apply{
                orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL;setPadding(dp(16),0,dp(16),0)
                background=shape(raised,if(connected)ok else line);isClickable=true;isFocusable=true;isEnabled=enabled;alpha=if(enabled)1f else .5f
                contentDescription="Connect to ${host.name}"
                setOnClickListener{if(isEnabled){session.pause();link.connect(host)}}
            }
            row.addView(text(host.name,15f),LinearLayout.LayoutParams(0,-2,1f))
            row.addView(text(if(connected)"Connected" else "Connect",13f,if(connected)ok else muted))
            list.addView(row,LinearLayout.LayoutParams(-1,dp(56)).apply{bottomMargin=dp(8)})
        }
        content.full(list)
        if(link.ready){
            content.space(4);content.full(button("Disconnect"){session.pause();link.disconnect()})
            content.space(8);content.full(button("Pair a new computer"){pairNewComputer()})
        }
        content.space(28);content.full(text("Keyboard and mouse only for now. Xbox-style gamepad output is a later milestone.",12f,muted))
        content.space(10)
        content.full(button("Connection details"){showDetails()})
    }

    private fun prepareBluetooth() {
        if(!allowed()&&Build.VERSION.SDK_INT>=31){requestPermissions(arrayOf(Manifest.permission.BLUETOOTH_CONNECT),10);return}
        if(link.status.stage=="disabled"){
            systemPrompt=true
            try{startActivityForResult(Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE),20)}
            catch(_:SecurityException){systemPrompt=false;Toast.makeText(this,"Allow Nearby devices in Android settings, then retry.",Toast.LENGTH_LONG).show()}
            catch(_:RuntimeException){systemPrompt=false;Toast.makeText(this,"Turn on Bluetooth in Settings.",Toast.LENGTH_LONG).show()}
        }else{link.stop();link.start()}
    }
    private fun pairNewComputer() {
        if(link.preview)return
        if(Build.VERSION.SDK_INT>=31&&checkSelfPermission(Manifest.permission.BLUETOOTH_ADVERTISE)!=PackageManager.PERMISSION_GRANTED){requestPermissions(arrayOf(Manifest.permission.BLUETOOTH_ADVERTISE),11);return}
        session.pause();systemPrompt=true;link.expectPairing()
        try{startActivityForResult(Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE).putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION,120),21)}
        catch(_:RuntimeException){systemPrompt=false;Toast.makeText(this,"Open Android Bluetooth settings to make this phone discoverable.",Toast.LENGTH_LONG).show()}
    }
    override fun onRequestPermissionsResult(requestCode:Int, permissions:Array<out String>, grantResults:IntArray){
        super.onRequestPermissionsResult(requestCode,permissions,grantResults)
        if(grantResults.isNotEmpty()&&grantResults.all{it==PackageManager.PERMISSION_GRANTED}){if(requestCode==11)pairNewComputer()else link.start()}
        else Toast.makeText(this,"Bluetooth permission is needed for direct connection.",Toast.LENGTH_LONG).show()
        renderPairing()
    }
    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?){super.onActivityResult(requestCode,resultCode,data);systemPrompt=false;if(allowed())link.start();renderPairing()}

    private fun openController() {
        if(!link.ready)return
        session.pause();inController=true
        requestedOrientation=ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
        renderController()
    }
    private fun renderController() {
        val page=shell(dark)
        val toolbar=LinearLayout(this).apply { orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL;setPadding(dp(12),dp(5),dp(12),dp(5)) }
        toolbar.addView(button("Back"){backToDevices()}.apply{id=R.id.back_to_devices},LinearLayout.LayoutParams(dp(76),dp(44)))
        val profile=Spinner(this)
        profile.adapter=ArrayAdapter(this,android.R.layout.simple_spinner_dropdown_item,ControlProfile.entries.map{it.title})
        profile.setSelection(session.profile.ordinal)
        profile.onItemSelectedListener=object:AdapterView.OnItemSelectedListener{
            override fun onNothingSelected(parent:AdapterView<*>?){}
            override fun onItemSelected(parent:AdapterView<*>?,view:View?,position:Int,id:Long){
                (view as? TextView)?.setTextColor(Color.rgb(239,236,225))
                if(session.profile.ordinal!=position){pauseInput();session.profile=ControlProfile.entries[position];surface?.invalidate()}
            }
        }
        toolbar.addView(profile,LinearLayout.LayoutParams(0,dp(44),1f))
        toolbar.addView(button("Controls"){showControls()},LinearLayout.LayoutParams(dp(100),dp(44)))
        toolbar.addView(button(if(session.active)"Stop" else "Play",true){if(session.active)pauseInput()else play()}.apply{id=R.id.play_stop},LinearLayout.LayoutParams(dp(90),dp(44)).apply{leftMargin=dp(8)})
        page.addView(toolbar)
        page.addView(text("",11f,Color.rgb(165,181,181)).apply{id=R.id.controller_status;setPadding(dp(18),0,dp(18),0)},LinearLayout.LayoutParams(-1,dp(25)))
        surface=ControllerSurface(this,session){pauseInput("Touch interrupted. Tap Play to continue.")}
        page.addView(surface,LinearLayout.LayoutParams(-1,0,1f))
        updateController()
    }
    private fun play() {
        if(!link.ready){pauseInput("Reconnect your computer first.");return}
        surface?.reset()
        if(session.start()){
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            if(gyroActive()){gyroTime=0;lastGyro=SystemClock.elapsedRealtime();sensors?.registerListener(this,gyro,SensorManager.SENSOR_DELAY_GAME)}
        }
        updateController()
    }
    private fun pauseInput(message:String?=null) {
        if(!::session.isInitialized)return
        session.pause();surface?.reset();sensors?.unregisterListener(this);gyroTime=0
        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        if(inController)updateController(message)
    }
    private fun updateController(message:String?=null) {
        if(!inController)return
        findViewById<Button>(R.id.play_stop)?.apply{
            text=if(session.active)"Stop" else "Play"
            background=if(session.active)shape(Color.TRANSPARENT,stopRed) else shape(ink)
            setTextColor(if(session.active)stopRed else bg)
        }
        findViewById<Button>(R.id.play_stop)?.isEnabled=link.ready
        findViewById<TextView>(R.id.controller_status)?.text=message?:if(session.active)"${link.status.host?.name} · Playing${if(gyroActive())" · Gyro assist" else ""}" else "Paused · focus your game on the PC, then tap Play"
    }
    private fun backToDevices() {
        pauseInput();inController=false;surface=null;requestedOrientation=ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED;renderPairing()
    }
    @Deprecated("Activity back navigation for the API 28 preview")
    override fun onBackPressed(){if(inController)backToDevices()else super.onBackPressed()}

    private fun showControls() {
        pauseInput()
        val body=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(22),dp(8),dp(22),dp(12))}
        body.full(text("Camera speed",14f))
        body.full(SeekBar(this).apply{max=25;progress=((session.lookSpeed-.5f)*10).toInt();setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener{
            override fun onStartTrackingTouch(bar:SeekBar?){};override fun onStopTrackingTouch(bar:SeekBar?){}
            override fun onProgressChanged(bar:SeekBar?,value:Int,fromUser:Boolean){session.lookSpeed=.5f+value/10f}
        })})
        body.full(CheckBox(this).apply{text="Third-person camera (hold right mouse)";isChecked=session.holdRight;setOnCheckedChangeListener{_,checked->session.holdRight=checked}})
        body.full(CheckBox(this).apply{text=if(gyro==null)"Gyro unavailable on this phone" else "Gyro assist while touching the look area";isEnabled=gyro!=null&&session.profile==ControlProfile.MOVE_LOOK;isChecked=gyroEnabled;setOnCheckedChangeListener{_,checked->gyroEnabled=checked}})
        body.full(CheckBox(this).apply{text="Invert gyro Y";isChecked=invertGyro;setOnCheckedChangeListener{_,checked->invertGyro=checked}})
        body.full(CheckBox(this).apply{text="Racing: proportional steering (pulses the arrow key)";isChecked=session.pulsedSteering;setOnCheckedChangeListener{_,checked->session.pulsedSteering=checked}})
        body.full(text("Movement uses 8-way keyboard directions. Turn off proportional steering for games that act once per key press (lane switchers, menus). Keep NONA open while playing. Stop before switching PC applications.",12f,muted))
        AlertDialog.Builder(this).setTitle("Controls").setView(body).setPositiveButton("Done"){_,_->preferences.edit().putFloat("lookSpeed",session.lookSpeed).putBoolean("holdRight",session.holdRight).putBoolean("invertGyro",invertGyro).putBoolean("pulsedSteering",session.pulsedSteering).apply();updateController()}.show()
    }
    private fun showDetails() {
        val report="NONA ${BuildConfig.VERSION_NAME}\n${Build.MANUFACTURER} ${Build.MODEL}\nAndroid ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})\nState: ${link.status.stage}\nHID registered: ${link.status.registered}\nHID connected: ${link.ready}\n${if(link.preview)"UI preview; no radio output" else link.status.message}"
        AlertDialog.Builder(this).setTitle("Connection details").setMessage(report).setPositiveButton("Copy"){_,_->(getSystemService(CLIPBOARD_SERVICE)as ClipboardManager).setPrimaryClip(ClipData.newPlainText("NONA connection",report))}.setNegativeButton("Close",null).show()
    }
    override fun onSensorChanged(event:SensorEvent){
        if(event.sensor.type!=Sensor.TYPE_GYROSCOPE||!session.active)return
        val dt=if(gyroTime==0L)0f else (event.timestamp-gyroTime)/1_000_000_000f
        gyroTime=event.timestamp;lastGyro=SystemClock.elapsedRealtime()
        if(surface?.lookHeld!=true)return
        val rotation=if(Build.VERSION.SDK_INT>=30)display?.rotation?:0 else windowManager.defaultDisplay.rotation
        val delta=MotionMath.gyro(event.values[0],event.values[1],rotation,dt)
        session.camera(delta.first,delta.second*if(invertGyro)-1 else 1)
    }
    override fun onAccuracyChanged(sensor:Sensor?,accuracy:Int){}
    private fun gyroActive()=gyroEnabled&&gyro!=null&&session.profile==ControlProfile.MOVE_LOOK
}
