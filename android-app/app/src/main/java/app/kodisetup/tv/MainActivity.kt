package app.kodisetup.tv

import android.os.Bundle
import android.os.Build
import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.tv.material3.*
import app.kodisetup.tv.model.SetupStep

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { KodiSetupTheme { SetupScreen() } }
    }
}

@Composable
private fun KodiSetupTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = darkColorScheme(primary = Color(0xFF52B8FF), background = Color(0xFF07111F), surface = Color(0xFF10233A)), content = content)
}

@Composable
private fun SetupScreen(model: SetupViewModel = viewModel()) {
    val state by model.state.collectAsStateWithLifecycle()
    val context = androidx.compose.ui.platform.LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val storagePermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted -> if (granted) model.prepareBootstrap() }
    DisposableEffect(lifecycleOwner, model) {
        val observer = LifecycleEventObserver { _, event -> if (event == Lifecycle.Event.ON_RESUME) model.resumeWorkflow() }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }
    Box(Modifier.fillMaxSize().background(Brush.linearGradient(listOf(Color(0xFF07111F), Color(0xFF14335A)))).padding(56.dp)) {
        Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
            Column {
                Text("STARLANE MERIDIAN", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Color(0xFF52B8FF))
                Spacer(Modifier.height(12.dp))
                Text(titleFor(state.step), fontSize = 40.sp, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(12.dp))
                Text(state.message, fontSize = 20.sp, color = Color(0xFFC8D8EB))
                state.error?.let { Spacer(Modifier.height(12.dp)); Text(it, color = Color(0xFFFF8A80), fontSize = 18.sp) }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(18.dp), verticalAlignment = Alignment.CenterVertically) {
                when (state.step) {
                    SetupStep.WELCOME -> PairingActions(model)
                    SetupStep.CONFIGURATION -> { Action("Start setup") { model.startAutomatedSetup() }; Action("Allow APK installs") { model.grantInstallPermission() }; Action("Install Kodi") { model.installKodi() } }
                    SetupStep.KODI -> Action("Install Proton VPN") { model.openProton() }
                    SetupStep.PROTON -> Action("Prepare Kodi bootstrap") { if (Build.VERSION.SDK_INT < 29 && ContextCompat.checkSelfPermission(context, Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) storagePermission.launch(Manifest.permission.WRITE_EXTERNAL_STORAGE) else model.prepareBootstrap() }
                    SetupStep.BOOTSTRAP -> Action("I installed the bootstrap") { model.continueToAccounts() }
                    SetupStep.ACCOUNT_LINK -> { Action("Link Real-Debrid") { model.beginRealDebrid() }; state.debridCode?.let { Text("Code: $it  ${state.debridUrl.orEmpty()}", fontSize = 18.sp) }; Action("Finish") { model.markComplete() } }
                    SetupStep.COMPLETE -> Text("Setup can now be monitored from the Windows portal.", fontSize = 18.sp)
                }
                if (state.busy) Text("Working…", color = Color(0xFF52B8FF), fontSize = 18.sp)
            }
            StepBar(state.step)
        }
    }
}

@Composable
private fun PairingActions(model: SetupViewModel) {
    var code by remember { mutableStateOf("") }
    BasicTextField(value = code, onValueChange = { value -> code = value.filter(Char::isDigit).take(8) }, singleLine = true,
        textStyle = androidx.compose.ui.text.TextStyle(color = Color.White, fontSize = 22.sp),
        modifier = Modifier.width(220.dp).background(Color(0xFF10233A)).padding(14.dp))
    Action("Pair TV") { model.pair(code) }
    Button(onClick = model::continueOffline, colors = ButtonDefaults.colors(containerColor = Color(0xFF294866))) { Text("Continue offline") }
}

@Composable private fun Action(label: String, action: () -> Unit) { Button(onClick = action) { Text(label, Modifier.padding(horizontal = 12.dp, vertical = 6.dp)) } }

@Composable
private fun StepBar(current: SetupStep) {
    val steps = listOf(SetupStep.WELCOME, SetupStep.CONFIGURATION, SetupStep.KODI, SetupStep.PROTON, SetupStep.BOOTSTRAP, SetupStep.COMPLETE)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { steps.forEach { Box(Modifier.height(5.dp).weight(1f).background(if (steps.indexOf(it) <= steps.indexOf(current)) Color(0xFF52B8FF) else Color(0xFF34506D))) } }
}

private fun titleFor(step: SetupStep) = when (step) {
    SetupStep.WELCOME -> "Set up this TV"
    SetupStep.CONFIGURATION -> "Configuration verified"
    SetupStep.KODI -> "Kodi installation"
    SetupStep.PROTON -> "Protect the connection"
    SetupStep.BOOTSTRAP -> "Apply the Kodi build"
    SetupStep.ACCOUNT_LINK -> "Link accounts"
    SetupStep.COMPLETE -> "Setup complete"
}
