package com.example.flutter_application_1

import android.graphics.Bitmap
import android.graphics.Matrix
import android.os.Bundle
import android.os.SystemClock
import android.util.Log
import android.widget.Toast
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker.HandLandmarkerOptions
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.util.concurrent.Executors

class MainActivity : FlutterActivity() {
    private val CHANNEL = "mediapipe_hand"
    private var handLandmarker: HandLandmarker? = null
    private val backgroundExecutor = Executors.newSingleThreadExecutor()
    // مصفوفة لإعادة استخدامها وتسريع الأداء
    private var argbArray: IntArray? = null 

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        // رسالة تظهر على شاشة الهاتف لتتأكد أن الكود الجديد وصل
        Toast.makeText(context, "قرب الكامرة على يدك", Toast.LENGTH_LONG).show()
        Log.e("HandScanner", "🚀 KOTLIN RESTARTED: RAW RGB MODE")

        setupMediaPipe()

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            if (call.method == "detectHand") {
                val planes = call.argument<List<ByteArray>>("planes")
                val width = call.argument<Int>("width") ?: 0
                val height = call.argument<Int>("height") ?: 0

                if (planes != null) {
                    backgroundExecutor.execute {
                        val landmarks = processImage(planes, width, height)
                        runOnUiThread { result.success(landmarks) }
                    }
                } else {
                    result.error("INVALID", "No Data", null)
                }
            }
        }
    }

    private fun setupMediaPipe() {
        try {
            // نستخدم CPU لأنه أكثر استقراراً مع Realme من GPU الذي به مشاكل تعريفات
            val baseOptions = BaseOptions.builder()
                .setModelAssetPath("hand_landmarker.task")
                .setDelegate(Delegate.CPU) 
                .build()

            val options = HandLandmarkerOptions.builder()
                .setBaseOptions(baseOptions)
                .setMinHandDetectionConfidence(0.1f) 
                .setNumHands(1)
                .setRunningMode(RunningMode.VIDEO)
                .build()

            handLandmarker = HandLandmarker.createFromOptions(context, options)
            Log.e("HandScanner", "✅ MediaPipe Initialized (CPU Mode)")
        } catch (e: Exception) {
            Log.e("HandScanner", "❌ Setup Error: ${e.message}")
        }
    }

    private fun processImage(planes: List<ByteArray>, width: Int, height: Int): List<Float>? {
        if (handLandmarker == null) return null

        try {
            // تحويل سريع جداً (بدون JPEG)
            // نأخذ مصفوفة YUV ونحولها لـ ARGB مباشرة
            if (argbArray == null || argbArray!!.size != width * height) {
                argbArray = IntArray(width * height)
            }
            
            // دالة التحويل اليدوي (أسرع من Bitmap Factory بـ 5 مرات)
            yuvToRgb(planes[0], planes[1], planes[2], width, height, argbArray!!)

            // إنشاء Bitmap من الألوان الجاهزة
            val bitmap = Bitmap.createBitmap(argbArray!!, width, height, Bitmap.Config.ARGB_8888)

            // تدوير 270
            val matrix = Matrix()
            matrix.postRotate(270f)
            matrix.postScale(-1f, 1f)
            val rotatedBitmap = Bitmap.createBitmap(bitmap, 0, 0, width, height, matrix, true)

            // إرسال للموديل
            val mpImage = BitmapImageBuilder(rotatedBitmap).build()
            val result = handLandmarker!!.detectForVideo(mpImage, SystemClock.uptimeMillis())

            if (result.landmarks().isNotEmpty()) {
                val hand = result.landmarks()[0]
                val points = mutableListOf<Float>()
                for (lm in hand) {
                    points.add(lm.x())
                    points.add(lm.y())
                    points.add(lm.z())
                }
                return points
            }
        } catch (e: Exception) {
            Log.e("HandScanner", "Processing Error: ${e.message}")
        }
        return null
    }

    // دالة تحويل رياضية سريعة جداً
    private fun yuvToRgb(yBytes: ByteArray, uBytes: ByteArray, vBytes: ByteArray, width: Int, height: Int, out: IntArray) {
        val yRowStride = yBytes.size / height
        val uvRowStride = uBytes.size / (height / 2)
        val uvPixelStride = if (uBytes.size >= (width/2)*(height/2)*2) 2 else 1

        for (y in 0 until height) {
            for (x in 0 until width) {
                val yIndex = y * yRowStride + x
                val uvIndex = (y / 2) * uvRowStride + (x / 2) * uvPixelStride
                
                // حماية من الخروج عن الحدود
                if (yIndex >= yBytes.size || uvIndex >= uBytes.size || uvIndex >= vBytes.size) continue

                val Y = (yBytes[yIndex].toInt() and 0xff)
                val U = (uBytes[uvIndex].toInt() and 0xff) - 128
                val V = (vBytes[uvIndex].toInt() and 0xff) - 128

                // معادلة YUV to RGB القياسية
                val r = (Y + 1.370705 * V).toInt().coerceIn(0, 255)
                val g = (Y - 0.698001 * V - 0.337633 * U).toInt().coerceIn(0, 255)
                val b = (Y + 1.732446 * U).toInt().coerceIn(0, 255)

                out[y * width + x] = (0xFF shl 24) or (r shl 16) or (g shl 8) or b
            }
        }
    }
}