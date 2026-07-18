plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

android {
    namespace = "app.kodisetup.tv"
    compileSdk = 36

    defaultConfig {
        applicationId = "app.kodisetup.tv"
        minSdk = 25
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
        buildConfigField("String", "MANIFEST_URL", "\"${providers.gradleProperty("manifestUrl").orNull ?: "https://github.com/rjclark99/starlanemeridian/releases/latest/download/manifest.json"}\"")
        buildConfigField("String", "MANIFEST_PUBLIC_KEY", "\"${providers.gradleProperty("manifestPublicKey").orNull ?: ""}\"")
        buildConfigField("String", "CONTROL_API_URL", "\"${providers.gradleProperty("controlApiUrl").orNull ?: "https://control.starlanemeridian.uk"}\"")
    }

    val releaseStoreFile = providers.gradleProperty("releaseStoreFile").orNull
    if (releaseStoreFile != null) {
        signingConfigs {
            create("release") {
                storeFile = rootProject.file(releaseStoreFile)
                storePassword = providers.gradleProperty("releaseStorePassword").get()
                keyAlias = providers.gradleProperty("releaseKeyAlias").get()
                keyPassword = providers.gradleProperty("releaseKeyPassword").get()
            }
        }
        buildTypes.getByName("release").signingConfig = signingConfigs.getByName("release")
    }

    buildFeatures { compose = true; buildConfig = true }
    packaging { resources.excludes += setOf("META-INF/DEPENDENCIES", "META-INF/LICENSE*") }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2026.06.00")
    implementation(composeBom)
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.2")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.2")
    implementation("androidx.tv:tv-material:1.1.0")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    implementation("com.google.crypto.tink:tink-android:1.18.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
}
