-dontwarn javax.annotation.processing.**
-dontwarn javax.lang.model.**
-dontwarn com.google.auto.value.**
# حماية مكتبات MediaPipe و TensorFlow من التغيير
-keep class com.google.mediapipe.** { *; }
-keep class com.google.protobuf.** { *; }
-keep class org.tensorflow.** { *; }

# حماية الدوال التي تتواصل مع لغة C++
-keepclassmembers class * {
    @com.google.mediapipe.framework.UsedByNative *;
}
-keepclassmembers class * {
    @com.google.mediapipe.framework.UsedByReflection *;
}
# حماية ملفات وبروتوكولات MediaPipe الداخلية من الحذف
-keep class com.google.mediapipe.proto.** { *; }
-dontwarn com.google.mediapipe.proto.**
-dontwarn com.google.mediapipe.**
# حماية أدوات جوجل الأساسية والتتبع (Flogger & Guava) من التشفير والدمج
-keep class com.google.common.** { *; }
-keep class com.google.common.flogger.** { *; }
-dontwarn com.google.common.**

# منع دمج (Inlining) الكلاسات التي تعتمد على تتبع المكدس
-keep,allowobfuscation,allowshrinking class com.google.mediapipe.framework.** { *; }