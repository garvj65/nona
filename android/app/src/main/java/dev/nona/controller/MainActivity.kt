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
    private val background = Color.rgb(244,242,237)
    private val ink = Color.rgb(32,41,43)
    private val muted = Color.rgb(102,113,113)
    private val accent = Color.rgb(185,81,56)
    private val dark = Color.rgb(21,31,33)
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
        setTextColor(if(primary)Color.WHITE else ink)
        background=shape(if(primary)accent else Color.rgb(232,232,225))
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
            // 100 Hz: smoother relative camera and 10 ms resolution for pulsed steering.
            handler.postDelayed(this,if(inController)10 else 1500)
        }
    }

    private fun shell(color: Int): LinearLayout {
        window.statusBarColor=color;window.navigationBarColor=color
        window.decorView.systemUiVisibility=if(color==background)View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR else 0
        root=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;setBackgroundColor(color) }
        root.setOnApplyWindowInsetsListener { view, insets ->
            if(Build.VERSION.SDK_INT>=30){val bars=insets.getInsets(WindowInsets.Type.systemBars());view.setPadding(bars.left,bars.top,bars.right,bars.bottom)}
            else view.setPadding(insets.systemWindowInsetLeft,insets.systemWindowInsetTop,insets.systemWindowInsetRight,insets.systemWindowInsetBottom)
            insets
        }
        setContentView(root);root.requestApplyInsets();return root
    }

    private fun renderPairing() {
        if(inController)return
        val outer=shell(background)
        val content=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;setPadding(dp(24),dp(22),dp(24),dp(24)) }
        val scroll=ScrollView(this);scroll.addView(content);outer.addView(scroll)
        content.full(text("NONA",20f).apply{typeface=Typeface.create("sans-serif-black",Typeface.NORMAL);letterSpacing=.08f})
        content.space(7);content.full(text(if(link.preview)"UI PREVIEW · NO BLUETOOTH OUTPUT" else "BLUETOOTH / ANDROID PREVIEW",10f,muted))
        content.space(30)
        content.full(text("Choose your\ncomputer.",38f).apply{typeface=Typeface.create("serif",Typeface.BOLD)})
        content.space(12);content.full(text("Your phone becomes a keyboard and mouse. No PC companion is needed for this mode.",15f,muted))
        content.space(22)
        content.full(text(link.status.message,15f).apply{id=R.id.link_status})
        content.space(12)
        if(!link.status.registered){
            val title=when{!allowed()->"Allow Bluetooth";link.status.stage=="disabled"->"Turn on Bluetooth";link.status.stage=="preparing"->"Retry Bluetooth setup";else->"Set up Bluetooth"}
            content.full(button(title,true){prepareBluetooth()}.apply{id=R.id.link_action})
        }else{
            content.full(button("Pair a new computer"){pairNewComputer()}.apply{id=R.id.link_action})
        }
        content.space(24);content.full(text("PAIRED DEVICES",10f,muted))
        val hosts=link.computers();hostsSignature=hosts.joinToString{it.address}
        val list=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;id=R.id.host_list}
        if(hosts.isEmpty())list.addView(text("On Windows, open Bluetooth settings → Add device → Bluetooth, then select this phone. Return here and choose your computer.",14f,muted))
        for(host in hosts){
            val connected=link.status.host?.address==host.address&&link.ready
            list.addView(button(if(connected)"${host.name} · Connected" else host.name){session.pause();link.connect(host)}.apply{
                isEnabled=link.status.registered&&link.status.stage!="connecting"
                contentDescription="Connect to ${host.name}"
            },LinearLayout.LayoutParams(-1,dp(52)).apply{bottomMargin=dp(8)})
        }
        content.full(list)
        if(link.ready){
            content.space(12);content.full(button("Open controller",true){openController()}.apply{id=R.id.open_controller})
            content.space(10);content.full(button("Disconnect"){session.pause();link.disconnect()})
        }
        content.space(28);content.full(text("Use keyboard/mouse controls in your game. Xbox controller emulation is not part of this Bluetooth preview.",12f,muted))
        content.space(8)
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
        findViewById<Button>(R.id.play_stop)?.text=if(session.active)"Stop" else "Play"
        findViewById<Button>(R.id.play_stop)?.isEnabled=link.ready
        findViewById<TextView>(R.id.controller_status)?.text=message?:if(session.active)"${link.status.host?.name} · Playing${if(gyroActive())" · Gyro assist" else ""}" else "Paused · Focus your game on the PC, then tap Play"
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
