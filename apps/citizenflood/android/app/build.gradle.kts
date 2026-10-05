plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val releaseStore = System.getenv("CITIZENFLOOD_KEYSTORE")
val releaseAlias = System.getenv("CITIZENFLOOD_KEY_ALIAS")
val releaseStorePassword = System.getenv("CITIZENFLOOD_STORE_PASSWORD")
val releaseKeyPassword = System.getenv("CITIZENFLOOD_KEY_PASSWORD")
val releaseConfigured = listOf(releaseStore, releaseAlias, releaseStorePassword, releaseKeyPassword).all { !it.isNullOrBlank() }
if (!releaseConfigured) {
    gradle.taskGraph.whenReady {
        if (allTasks.any { it.project == project && it.name.contains("release", ignoreCase = true) }) {
            throw GradleException("Release signing is required. Use the documented release builder; debug signing is never a release fallback.")
        }
    }
}

android {
    namespace = "au.edu.monash.citizenflood"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        manifestPlaceholders["appAuthRedirectScheme"] = "au.edu.monash.citizenflood"
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "au.edu.monash.citizenflood"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (releaseConfigured) {
            create("release") {
                storeFile = file(releaseStore!!)
                keyAlias = releaseAlias
                storePassword = releaseStorePassword
                keyPassword = releaseKeyPassword
            }
        }
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".staging"
            versionNameSuffix = "-staging"
        }
        release {
            if (releaseConfigured) signingConfig = signingConfigs.getByName("release")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
