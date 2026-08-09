package app.kodisetup.tv

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
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
    MaterialTheme(colorScheme = darkColorScheme(primary = Color(0xFF61C8FF), secondary = Color(0xFF67E8C4), background = Color(0xFF050B14), surface = Color(0xFF102A42)), content = content)
}

@Composable
private fun SetupScreen(model: SetupViewModel = viewModel()) {
    val state by model.state.collectAsStateWithLifecycle()
    val context = androidx.compose.ui.platform.LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val primaryFocus = remember { FocusRequester() }
    val storagePermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) model.prepareBootstrap() else model.storagePermissionDenied()
    }
    DisposableEffect(lifecycleOwner, model) {
        val observer = LifecycleEventObserver { _, event -> if (event == Lifecycle.Event.ON_RESUME) model.resumeWorkflow() }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }
    LaunchedEffect(state.step, state.busy) {
        if (!state.busy) runCatching { primaryFocus.requestFocus() }
    }
    if (state.consentGeneration != null) {
        ConsentScreen(state.consentScope, model::cancelAutomationConsent, model::grantAutomationConsent)
        return
    }
    Box(Modifier.fillMaxSize().background(Brush.linearGradient(listOf(Color(0xFF050B14), Color(0xFF102A42)))).padding(56.dp)) {
        Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
            Column {
                Text("STARLANE MOVIES", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Color(0xFF67E8C4))
                Spacer(Modifier.height(12.dp))
                Text(titleFor(state.step), fontSize = 40.sp, fontWeight = FontWeight.SemiBold, color = Color.White)
                Spacer(Modifier.height(12.dp))
                Text(state.message, fontSize = 20.sp, color = Color(0xFFC8D8EB))
                state.error?.let { Spacer(Modifier.height(12.dp)); Text(it, color = Color(0xFFFF8A80), fontSize = 18.sp) }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(18.dp), verticalAlignment = Alignment.CenterVertically) {
                when (state.step) {
                    SetupStep.WELCOME -> PairingActions(model, primaryFocus)
                    SetupStep.CONFIGURATION -> { Action("Start setup", Modifier.focusRequester(primaryFocus)) { model.startAutomatedSetup() }; Action("Allow APK installs") { model.grantInstallPermission() }; Action("Install Kodi") { model.installKodi() } }
                    SetupStep.KODI -> Action("Install Proton VPN", Modifier.focusRequester(primaryFocus)) { model.openProton() }
                    SetupStep.PROTON -> Action("Prepare Kodi bootstrap", Modifier.focusRequester(primaryFocus)) { if (Build.VERSION.SDK_INT < 29 && ContextCompat.checkSelfPermission(context, Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) storagePermission.launch(Manifest.permission.WRITE_EXTERNAL_STORAGE) else model.prepareBootstrap() }
                    SetupStep.BOOTSTRAP -> {
                        Action("Check applied setup", Modifier.focusRequester(primaryFocus)) { model.checkBootstrapApplied() }
                        if (!state.automationRunning) {
                            Action("Resume automated setup") { model.resumeAutomatedBootstrap() }
                        }
                    }
                    SetupStep.ACCOUNT_LINK -> { Action("Link Real-Debrid", Modifier.focusRequester(primaryFocus)) { model.beginRealDebrid() }; state.debridCode?.let { Text("Code: $it  ${state.debridUrl.orEmpty()}", color = Color.White, fontSize = 18.sp) }; Action("Finish") { model.markComplete() } }
                    SetupStep.COMPLETE -> {
                        Action("Prepare Kodi bootstrap", Modifier.focusRequester(primaryFocus)) {
                            if (Build.VERSION.SDK_INT < 29 && ContextCompat.checkSelfPermission(context, Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                                storagePermission.launch(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                            } else {
                                model.prepareBootstrap()
                            }
                        }
                        Text("Setup can now be monitored by your setup provider.", color = Color.White, fontSize = 18.sp)
                    }
                }
                if (state.automationRunning) Action("Stop automated setup") { model.stopAutomatedSetup() }
                if (state.busy) Text("Working...", color = Color(0xFF61C8FF), fontSize = 18.sp)
            }
            StepBar(state.step)
        }
    }
}

@Composable
private fun ConsentScreen(scope: app.kodisetup.tv.automation.AutomationScope?, cancel: () -> Unit, approve: () -> Unit) {
    val cancelFocus = remember { FocusRequester() }
    var confirming by remember(scope) { mutableStateOf(false) }
    LaunchedEffect(scope, confirming) { runCatching { cancelFocus.requestFocus() } }
    Box(Modifier.fillMaxSize().background(Brush.linearGradient(listOf(Color(0xFF050B14), Color(0xFF102A42)))).padding(56.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text(if (confirming) "Confirm full automation" else "Full automation warning", fontSize = 38.sp, fontWeight = FontWeight.SemiBold, color = Color.White)
            Text("Requested scope: ${scope?.name ?: "UNKNOWN"}", fontSize = 18.sp, color = Color(0xFF67E8C4))
            Text("Automated after approval: download and verify configured packages, open an official app-store route when needed, and on Android 9 or older atomically enable Kodi Unknown Sources and install only the verified Starlane Bootstrap repository.", fontSize = 19.sp, color = Color(0xFFC8D8EB))
            Text("Always manual and visible: Android storage/install permissions, every package/store confirmation, and Bootstrap's separate approval inside Kodi. Android 10+ also keeps Kodi Unknown Sources, ZIP selection, and Install from ZIP manual.", fontSize = 19.sp, color = Color(0xFFC8D8EB))
            Text("Consent applies only to this app/configuration and this run, expires within 24 hours, and can be stopped at any time.", fontSize = 19.sp, color = Color(0xFFC8D8EB))
            if (confirming) Text("This is the secondary confirmation. Approve only if you want Starlane Movies to perform the fixed automated steps described above.", fontSize = 19.sp, color = Color(0xFFFFD58A))
            Row(horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                Action("Cancel", Modifier.focusRequester(cancelFocus), cancel)
                if (confirming) Action("Confirm and approve one run", action = approve)
                else Action("Continue to confirmation") { confirming = true }
            }
        }
    }
}

@Composable
private fun PairingActions(model: SetupViewModel, initialFocus: FocusRequester) {
    var code by remember { mutableStateOf("") }
    val pairButtonFocus = remember { FocusRequester() }
    BasicTextField(value = code, onValueChange = { value -> code = value.filter(Char::isDigit).take(8) }, singleLine = true,
        textStyle = androidx.compose.ui.text.TextStyle(color = Color.White, fontSize = 22.sp),
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number, imeAction = ImeAction.Done),
        keyboardActions = KeyboardActions(onDone = { pairButtonFocus.requestFocus() }),
        modifier = Modifier.focusRequester(initialFocus).width(220.dp).background(Color(0xFF10233A)).border(2.dp, Color(0xFF34506D)).padding(14.dp),
        decorationBox = { input -> Box { if (code.isEmpty()) Text("8-digit pairing code", color = Color(0xFF8FA6BF), fontSize = 18.sp); input() } })
    Action("Pair TV", Modifier.focusRequester(pairButtonFocus)) { model.pair(code) }
    Button(onClick = model::continueOffline, colors = ButtonDefaults.colors(containerColor = Color(0xFF294866))) { Text("Continue offline", color = Color.White, fontSize = 18.sp) }
}

@Composable
private fun Action(label: String, modifier: Modifier = Modifier, action: () -> Unit) {
    Button(
        onClick = action,
        modifier = modifier,
        colors = ButtonDefaults.colors(
            containerColor = Color(0xFF294866),
            focusedContainerColor = Color(0xFF1B5573),
            pressedContainerColor = Color(0xFF153F57),
        ),
    ) {
        Text(label, Modifier.padding(horizontal = 12.dp, vertical = 6.dp), color = Color.White, fontSize = 18.sp)
    }
}

@Composable
private fun StepBar(current: SetupStep) {
    val steps = listOf(SetupStep.WELCOME, SetupStep.CONFIGURATION, SetupStep.KODI, SetupStep.PROTON, SetupStep.BOOTSTRAP, SetupStep.COMPLETE)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { steps.forEach { Box(Modifier.height(5.dp).weight(1f).background(if (steps.indexOf(it) <= steps.indexOf(current)) Color(0xFF61C8FF) else Color(0xFF34506D))) } }
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
