import 'dart:async';
import 'dart:math'; 
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:flutter_tts/flutter_tts.dart'; 
import 'settings_manager.dart';
import 'package:url_launcher/url_launcher.dart';

late List<CameraDescription> cameras; //empty var for camera

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized(); //make shure that flutter engin is working
  try {
    cameras = await availableCameras(); // searching for cameras ...
  } on CameraException catch (e) {
    print('Camera Error: $e'); // if there are no avalibl cams 
  }
  runApp(const MaterialApp(  // run the app
    debugShowCheckedModeBanner: false,  // hide debug banner
    home: HomePage(), // first widget is signlam..etc
  ));
}


// ==========================================
// 1. main page 
// ==========================================

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  AppSettings _settings = AppSettings();
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final loadedSettings = await SettingsManager.loadSettings();
    setState(() {
      _settings = loadedSettings;
    });
  }

  Future<void> _saveSettings() async {
    await SettingsManager.saveSettings(_settings);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: const Color(0xFF2E2E2E),
      // Drawer configuration
      endDrawer: Drawer(
        backgroundColor: const Color(0xFF333333),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const Text("الإعدادات", style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
              const Divider(color: Colors.white24, thickness: 2),
              
              // 1. Capture Speed (Stability Frames)
              _buildSliderTitle("سرعة الالتقاط (إطارات)", _settings.stabilityFrames.toString()),
              Slider(
                value: _settings.stabilityFrames.toDouble(),
                min: 1, max: 10, divisions: 9,
                activeColor: Colors.cyanAccent,
                onChanged: (val) { setState(() => _settings.stabilityFrames = val.toInt()); _saveSettings(); },
              ),

              // 2. Confidence Threshold
              _buildSliderTitle("دقة التعرف", "${(_settings.confidenceThreshold * 100).toInt()}%"),
              Slider(
                value: _settings.confidenceThreshold,
                min: 0.1, max: 0.9, divisions: 8,
                activeColor: Colors.cyanAccent,
                onChanged: (val) { setState(() => _settings.confidenceThreshold = val); _saveSettings(); },
              ),

              // 3. Movement Sensitivity
              _buildSliderTitle("حساسية الحركة", _settings.stabilityThreshold.toStringAsFixed(3)),
              Slider(
                value: _settings.stabilityThreshold,
                min: 0.01, max: 0.1, divisions: 9,
                activeColor: Colors.cyanAccent,
                onChanged: (val) { setState(() => _settings.stabilityThreshold = val); _saveSettings(); },
              ),

              // 4. Speech Rate
              _buildSliderTitle("سرعة الصوت", _settings.speechRate.toStringAsFixed(1)),
              Slider(
                value: _settings.speechRate,
                min: 0.1, max: 1.5, divisions: 14,
                activeColor: Colors.greenAccent,
                onChanged: (val) { setState(() => _settings.speechRate = val); _saveSettings(); },
              ),

              // 5. Speech Pitch
              _buildSliderTitle("حدة الصوت", _settings.speechPitch.toStringAsFixed(1)),
              Slider(
                value: _settings.speechPitch,
                min: 0.5, max: 2.0, divisions: 15,
                activeColor: Colors.greenAccent,
                onChanged: (val) { setState(() => _settings.speechPitch = val); _saveSettings(); },
              ),

              const Divider(color: Colors.white24),

              // 6. Allow Repetition
              SwitchListTile(
                title: const Text("السماح بتكرار الحروف", style: TextStyle(color: Colors.white), textAlign: TextAlign.right),
                activeColor: Colors.cyanAccent,
                value: _settings.allowRepetition,
                onChanged: (val) { setState(() => _settings.allowRepetition = val); _saveSettings(); },
              ),

              // 7. Auto Speak
              SwitchListTile(
                title: const Text("النطق التلقائي للإشارة", style: TextStyle(color: Colors.white), textAlign: TextAlign.right),
                activeColor: Colors.cyanAccent,
                value: _settings.autoSpeak,
                onChanged: (val) { setState(() => _settings.autoSpeak = val); _saveSettings(); },
              ),
            ],
          ),
        ),
      ),
      appBar: AppBar(
        title: const Text("مترجم لغة الإشارة", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: const Color(0xFF333333),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white),
            onPressed: () => _scaffoldKey.currentState?.openEndDrawer(), // Open drawer from right
          )
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.back_hand_rounded, size: 100, color: Color.fromARGB(255, 105, 233, 240)),
              const SizedBox(height: 20),
              const Text("أهلاً بك في مترجم الإشارة", style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
              const SizedBox(height: 50),

              // Pass settings to Scanner
              _buildMenuButton(context, title: "ابدأ الترجمة", icon: Icons.camera_alt, color: const Color.fromARGB(255, 105, 233, 240), onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (context) => SignLanguageScanner(settings: _settings)));
              }),
              _buildMenuButton(context, title: "تعلم الحركات", icon: Icons.school, color: Colors.blueAccent, onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (context) => const LearnPage()));
              }),
              _buildMenuButton(context, title: "عن التطبيق", icon: Icons.info_outline, color: const Color.fromARGB(255, 104, 237, 173), onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (context) => const AboutPage()));
              }),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSliderTitle(String title, String value) {
    return Padding(
      padding: const EdgeInsets.only(top: 10, bottom: 5),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(value, style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold)),
          Text(title, style: const TextStyle(color: Colors.white70)),
        ],
      ),
    );
  }

  Widget _buildMenuButton(BuildContext context, {required String title, required IconData icon, required Color color, required VoidCallback onTap}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 10),
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF444444),
          padding: const EdgeInsets.symmetric(vertical: 15),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
          side: BorderSide(color: color, width: 2),
        ),
        onPressed: onTap,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color),
            const SizedBox(width: 15),
            Text(title, style: const TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}

// ==========================================
// about the app
// ==========================================

class AboutPage extends StatelessWidget {
  const AboutPage({Key? key}) : super(key: key);

  // دالة فتح رابط GitHub
  Future<void> _launchURL(String urlString) async {
    final Uri url = Uri.parse(urlString);
    if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
      debugPrint('Could not launch $urlString');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A1A), 
      appBar: AppBar(
        title: const Text("عن التطبيق", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontFamily: 'Cairo')),
        centerTitle: true,
        backgroundColor: const Color(0xFF222222),
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Align(
              alignment: Alignment.center,
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white10,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.greenAccent, width: 2),
                ),
                child: const Icon(Icons.psychology, size: 60, color: Colors.greenAccent),
              ),
            ),
            const SizedBox(height: 20),

            //titel
            const Text(
              "مترجم لغة الإشارة الذكي",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold, fontFamily: 'Cairo'),
            ),
            const SizedBox(height: 35),

            // project message
            _buildModernCard(
              title: "رسالة المشروع",
              icon: Icons.volunteer_activism,
              color: Colors.pinkAccent,
              content: "هذا التطبيق هو مشروع مستقل تم تطويره بهدف إنساني بحت لتسهيل التواصل. التطبيق مجاني بالكامل، وخالٍ تماماً من أي إعلانات تجارية، ليكون أداة مساعدة لكل من يحتاجها دون أي قيود.",
            ),
            const SizedBox(height: 15),

           //privicy section
            _buildModernCard(
              title: "أمان البيانات والخصوصية",
              icon: Icons.security, 
              color: Colors.greenAccent,
              content: "التطبيق يعمل بشكل محلي 100% (Offline) وبدون الحاجة لأي اتصال بالإنترنت. لا توجد أي حركة للبيانات نهائياً، ولا يتم إرسال أي معلومات لأي جهة.\n\nلم يتم استعمال أي نماذج جاهزة تعمل في سيرفرات خارجية بل تم برمجة وتدريب نموذج الذكاء الاصطناعي الخاص من الصفر خصيصاً لهذا المشروع لضمان الاستقلالية التامة والخصوصية المطلقة.",
            ),
            const SizedBox(height: 30),

            // sourc code button(GitHub)
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF252525),
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                side: const BorderSide(color: Colors.white24, width: 1),
              ),
              icon: const Icon(Icons.code, color: Colors.white),
              label: const Text("المصدر البرمجي (GitHub)", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold, fontFamily: 'Cairo')),
              onPressed: () => _launchURL("https://github.com/sjadgg/grup-3-GP"), // ضع رابط القت هب هنا
            ),

            const SizedBox(height: 40),
            
            // devolped by
            const Divider(color: Colors.white12),
            const SizedBox(height: 15),
            const Text(
              "طُور بواسطة",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white54, fontSize: 14, fontFamily: 'Cairo'),
            ),
            const SizedBox(height: 5),
            const Text(
              "SJAD",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.greenAccent, fontSize: 20, fontWeight: FontWeight.bold, fontFamily: 'Cairo'),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildModernCard({required String title, required IconData icon, required Color color, required String content}) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF252525),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10, width: 1),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        textDirection: TextDirection.rtl,
        children: [
          Row(
            textDirection: TextDirection.rtl,
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  title,
                  textAlign: TextAlign.right,
                  style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.bold, fontFamily: 'Cairo'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            content,
            style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.8, fontFamily: 'Cairo'),
            textAlign: TextAlign.right,
            textDirection: TextDirection.rtl,
          ),
        ],
      ),
    );
  }
}

// ==========================================
// 3. learn page
// ==========================================
class LearnPage extends StatelessWidget {
  const LearnPage({Key? key}) : super(key: key);
  final List<String> letters = const ["أ", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "هـ", "و", "ي","ة", "ال", "لا"];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF2E2E2E),
      appBar: AppBar(title: const Text("تعلم الحركات", style: TextStyle(color: Colors.white)), backgroundColor: const Color(0xFF333333), iconTheme: const IconThemeData(color: Colors.white)),
      body: GridView.builder(
        padding: const EdgeInsets.all(10),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, crossAxisSpacing: 10, mainAxisSpacing: 10, childAspectRatio: 0.8),
        itemCount: letters.length,
        itemBuilder: (context, index) {
          return Card(
            color: const Color(0xFF444444),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // alphabet
                Text(
                  letters[index],
                  style: const TextStyle(color: Color.fromARGB(255, 105, 233, 240), fontSize: 30, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 10),
                
                // show imgs 
                Expanded(
                  child: Container(
                    margin: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white, // white background
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(5.0),
                      child: Image.asset(
                        'assets/images/$index.png', // we got imgs orderd 0 , 1 , 2 .....
                        fit: BoxFit.contain, // fit the img
                        errorBuilder: (context, error, stackTrace) {
                          // if there are no imgs just show error red icon 
                          return const Icon(Icons.image_not_supported, color: Colors.red, size: 40);
                        },
                      ),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}



class SignLanguageScanner extends StatefulWidget {
  final AppSettings settings; // استلام الإعدادات
  const SignLanguageScanner({Key? key, required this.settings}) : super(key: key);

  @override
  State<SignLanguageScanner> createState() => _SignLanguageScannerState();
}

class _SignLanguageScannerState extends State<SignLanguageScanner> {
  CameraController? _controller;
  String _currentSentence = "";
  String _debugStatus = " loading ...";
  
  Interpreter? _interpreter;
  FlutterTts flutterTts = FlutterTts();
  static const platform = MethodChannel('mediapipe_hand');
  
  bool _isBusy = false;
  DateTime _lastFrameTime = DateTime.now();

  // --------------------------------
  // SYSTEM VARS (Now coming from widget.settings!)
  // -------------------------------
  final int HAND_GONE_FRAMES = 20;         
  final double EMA_ALPHA = 0.3;

  String _currentState = "MOVING";
  int _stableCounter = 0;
  List<double>? _lastHandShape;
  int _handGoneCounter = 0;
  double _smoothedDistance = 0.0;
  String _lastPredictedLetter = "";
  bool _spaceAdded = false;
  List<double>? _currentLandmarks; 

  final List<String> LABELS = [
    "أ", "ال", "ب", "ة", "ت", "ث", "ج", "ح", "خ", "د", 
    "ذ", "ر", "ز", "س", "ش", "ص", "ض", "ط", "ظ", "ع", 
    "غ", "ف", "ق", "ك", "ل", "لا", "م", "ن", "هـ", "و", "ي"
  ];
  
  // نفس المصفوفات الخاصة بك SCALER_MEAN و SCALER_SCALE تبدأ هنا
  final List<double> SCALER_MEAN = [
    0.44323240258325153, 0.7373397234890552, 4.281831895373044e-07, 0.5508517339852428, 0.6612059994757292, -0.04738079819027164, 0.6127256913003946, 0.5543237971539207, -0.07657821165590888, 0.6230260664824708, 0.47390455574205737, -0.10733442996156793, 0.6120591847859262, 0.4268166833356245, -0.13415350010773933, 0.5064699172826544, 0.4328860728548846, -0.044889163025152654, 0.5451476053994027, 0.3515403026311545, -0.10699777627114611, 0.5747950124630076, 0.3317282579540587, -0.14556603980142155, 0.5937090614713892, 0.31976609888365193, -0.1666760241703431, 0.4348511433780803, 0.44845714496387373, -0.056515196999313226, 0.5021235613525687, 0.38252992080821197, -0.129049205105761, 0.5497834516563457, 0.41080773629664097, -0.15510941453006952, 0.5739622589226193, 0.4241187745326882, -0.16038463429771913, 0.378186482148195, 0.4866319720905061, -0.0757547555951538, 0.44736284452717506, 0.44848572293836353, -0.15067857060838533, 0.47996217610884456, 0.49823584665383136, -0.14902908562176062, 0.485175856505503, 0.5214623851363895, -0.13082560141108152, 0.33090778252019293, 0.5388557257447621, -0.09942959761287416, 0.3876026432572365, 0.5030963911319367, -0.1489838626310367, 0.41529417295601123, 0.5240820415124178, -0.140067893923841, 0.41826280941547667, 0.5310071277798487, -0.12242933971756477
  ];
  final List<double> SCALER_SCALE = [
    0.1434039336822038, 0.11394195112234844, 1.016862023237553e-06, 0.13582046385759325, 0.10079877631703023, 0.050008798989503396, 0.12499543753731841, 0.09504405159002656, 0.06974639246234053, 0.11427654440548128, 0.10597953607104565, 0.08405856813979667, 0.14000748296234167, 0.13095285252676273, 0.09996304693387179, 0.11949564641124798, 0.0790228341134506, 0.07924832480481253, 0.12196813500421659, 0.07695484717120014, 0.09953978213774008, 0.13129867421844807, 0.09479549886918137, 0.10810651622373725, 0.14881838442040657, 0.12684855612403056, 0.11385658210791007, 0.0969420277875855, 0.08597206633645427, 0.0714924338381226, 0.08798372712205613, 0.10175477595268972, 0.09387525001261422, 0.10877077922602536, 0.1323082761321768, 0.09418734582570087, 0.13766061188620876, 0.16479715479025117, 0.09461781524423826, 0.08762787885490175, 0.10188492761469109, 0.06942287275082658, 0.09848227729472057, 0.11012204284320927, 0.08705780904959788, 0.10348121269945608, 0.12851613086861755, 0.07917705003248365, 0.11454475251317758, 0.1548560580455693, 0.07798709225580738, 0.10138748766588854, 0.11762899315152338, 0.07579594303663424, 0.1245314149257595, 0.12217738686069445, 0.08552575203372927, 0.13095468376131025, 0.1370906933735469, 0.08141606410295842, 0.13864676581155097, 0.1605851270020338, 0.08185649252455954
  ];

  @override
  void initState() { 
    super.initState();
    _setupSystem();
  }

  Future<void> _setupSystem() async { 
    await _initTTS();
    await _loadModel();
    await _initCamera();
  }

  Future<void> _initTTS() async {
    await flutterTts.setLanguage("ar-SA"); 
    await flutterTts.setPitch(widget.settings.speechPitch); // استخدام الإعدادات
    await flutterTts.setSpeechRate(widget.settings.speechRate); // استخدام الإعدادات
  }

  Future<void> _loadModel() async { 
    try {
      final modelData = await rootBundle.load('assets/asl_model_mobile.tflite');
      final Uint8List modelBytes = modelData.buffer.asUint8List();
      final options = InterpreterOptions();
      _interpreter = await Interpreter.fromBuffer(modelBytes, options: options);
      setState(() => _debugStatus = "model is ready !");
    } catch (e) {
      setState(() => _debugStatus = "model error: $e");
    }
  }

  Future<void> _initCamera() async { 
    if (cameras.isEmpty) return;
    final frontCamera = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );

    _controller = CameraController(
      frontCamera,
      ResolutionPreset.low,
      enableAudio: false,
      imageFormatGroup: Platform.isAndroid ? ImageFormatGroup.yuv420 : ImageFormatGroup.bgra8888,
    );

    await _controller!.initialize();
    
    _controller!.startImageStream((image) {
      if (!_isBusy) {
        if (DateTime.now().difference(_lastFrameTime).inMilliseconds > 50) {
           _isBusy = true;
           _lastFrameTime = DateTime.now();
           _processFrame(image);
        }
      }
    });
    
    if (mounted) setState(() {}); 
  }

  Future<void> _processFrame(CameraImage image) async {
    try {
      final List<Uint8List> planes = image.planes.map((plane) => plane.bytes).toList();
      final List<dynamic>? landmarksRaw = await platform.invokeMethod('detectHand', {
        'planes': planes,
        "width": image.width,
        "height": image.height,
      });

      if (landmarksRaw != null && landmarksRaw.length == 63) {
        List<double> landmarks = landmarksRaw.map((e) => (e as num).toDouble()).toList();
        
        setState(() {
          _currentLandmarks = landmarks;
        });

        // Calculate hand and fingers movement
        List<double> currentHandShape = [
          landmarks[0], landmarks[1],
          landmarks[4 * 3], landmarks[4 * 3 + 1],
          landmarks[8 * 3], landmarks[8 * 3 + 1],
          landmarks[12 * 3], landmarks[12 * 3 + 1]
        ];

        double distance = 0.0;
        if (_lastHandShape != null) { 
          double maxPointDistance = 0.0;
          for (int i = 0; i < currentHandShape.length; i += 2) {
            double pointDistance = sqrt(pow(currentHandShape[i] - _lastHandShape![i], 2) + pow(currentHandShape[i+1] - _lastHandShape![i+1], 2));
            if (pointDistance > maxPointDistance) {
              maxPointDistance = pointDistance;
            }
          }
          distance = maxPointDistance;
        }
        _lastHandShape = currentHandShape; 
        
        _smoothedDistance = (EMA_ALPHA * distance) + ((1 - EMA_ALPHA) * _smoothedDistance); 

        // استخدام المتغير القادم من الإعدادات
        if (_smoothedDistance < widget.settings.stabilityThreshold) { 
          _stableCounter++;
        } else {
          _stableCounter = 0;
          _currentState = "MOVING";
          _lastPredictedLetter = "";
          setState(() => _debugStatus = "hand moving !");
        }

        // استخدام المتغير القادم من الإعدادات
        if (_currentState == "MOVING" && _stableCounter > widget.settings.stabilityFrames) {
          List<double> input = [];
          for (int i = 0; i < landmarks.length; i += 3) {
             double x = landmarks[i];     
             double y = landmarks[i + 1];
             double z = landmarks[i + 2];

             double scaleX = SCALER_SCALE[i] == 0 ? 1.0 : SCALER_SCALE[i];
             double scaleY = SCALER_SCALE[i+1] == 0 ? 1.0 : SCALER_SCALE[i+1];
             double scaleZ = SCALER_SCALE[i+2] == 0 ? 1.0 : SCALER_SCALE[i+2];

             input.add((x - SCALER_MEAN[i]) / scaleX);
             input.add((y - SCALER_MEAN[i+1]) / scaleY);
             input.add((z - SCALER_MEAN[i+2]) / scaleZ);
          }
          var output = List.filled(LABELS.length, 0.0).reshape([1, LABELS.length]);
          _interpreter!.run([input], output);

          List<double> scores = List<double>.from(output[0]);
          double maxScore = scores.reduce(max);
          int maxIdx = scores.indexOf(maxScore);
          
          // print("Hand: ${LABELS[maxIdx]} ($maxScore)");

          // استخدام المتغير القادم من الإعدادات
          if (maxScore > widget.settings.confidenceThreshold) {
            String predictedLetter = LABELS[maxIdx];
            
            // استخدام المتغير القادم من الإعدادات (السماح بالتكرار)
            if (widget.settings.allowRepetition || predictedLetter != _lastPredictedLetter) {
              setState(() {
                _currentSentence += predictedLetter;
                _debugStatus = "detected : $predictedLetter";
              });
              _lastPredictedLetter = predictedLetter;
            }
          }
          _currentState = "STABLE"; 
        }
        _handGoneCounter = 0;
        _spaceAdded = false;

      } else {
        setState(() {
          _currentLandmarks = null;
        });

        if (_handGoneCounter < 100) _handGoneCounter++;
        if (_handGoneCounter > HAND_GONE_FRAMES && !_spaceAdded) {
            // التحقق من إعداد النطق التلقائي
            if (widget.settings.autoSpeak) {
               _speakFullSentence();
            }
            _stableCounter = 0;
            _currentState = "MOVING";
            _lastPredictedLetter = ""; 
            _lastHandShape = null;

            if (_currentSentence.isNotEmpty && !_currentSentence.endsWith(" ")) {
               setState(() {
                 _currentSentence += " ";
               });
            }
            _spaceAdded = true;
        }
      }

    } catch (e) {
      print("Error: $e");
    } finally {
      _isBusy = false;
    }
  }

  void _speakFullSentence() { 
    if (_currentSentence.trim().isNotEmpty) {
      flutterTts.speak(_currentSentence.trim());
    }
  }

  void _clearText() {
    setState(() {
      _currentSentence = "";
      _lastPredictedLetter = "";
      _spaceAdded = true;
    });
  }

  void _backspace() {
    if (_currentSentence.isNotEmpty) {
      setState(() {
        _currentSentence = _currentSentence.substring(0, _currentSentence.length - 1);
        _lastPredictedLetter = "";
        _spaceAdded = true;
      });
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    _interpreter?.close();
    flutterTts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    var cameraSize = _controller!.value.previewSize!; 

    return Scaffold(
      backgroundColor: const Color.fromARGB(255, 0, 0, 0), 
      appBar: AppBar(
        title: const Text("deaf talk",style: TextStyle(color: Colors.white),),
        centerTitle: true,
        backgroundColor: const Color.fromARGB(255, 48, 48, 48),
        actions: [
          IconButton(icon: const Icon(Icons.volume_up), onPressed: _speakFullSentence),
          IconButton(icon: const Icon(Icons.delete), onPressed: _clearText),
        ],
      ),
      body: Column( 
        children: [
          Expanded(
            flex: 5,
            child: Container(
              width: double.infinity,
              color: Colors.black,
              child: ClipRect(
                child: Stack(
                  fit: StackFit.expand, 
                  children: [
                    FittedBox(
                      fit: BoxFit.cover, 
                      child: SizedBox(
                        width: cameraSize.height, 
                        height: cameraSize.width,
                        child: Transform(
                          alignment: Alignment.center,
                          transform: Matrix4.rotationY(pi), 
                          child: CameraPreview(_controller!),
                        ),
                      ),
                    ),
                    if (_currentLandmarks != null)
                      CustomPaint(
                        painter: HandPainter(_currentLandmarks!),
                      ),
                  ],
                ),
              ),
            ),
          ),
          Expanded(
            flex: 2,
            child: Container(
              width: double.infinity,
              margin: const EdgeInsets.symmetric(horizontal: 5),
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF252525),
                border: Border.all(color: Colors.black, width: 2),
              ),
              child: SingleChildScrollView(
                reverse: true,
                child: Text(
                  _currentSentence,
                  textAlign: TextAlign.right,
                  textDirection: TextDirection.rtl,
                  style: const TextStyle(
                    color: Colors.green,
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(8),
            color: const Color(0xFF333333),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    _debugStatus, 
                    style: const TextStyle(color: Color.fromARGB(255, 62, 62, 62), fontSize: 12),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.backspace, color: Colors.redAccent),
                  onPressed: _backspace,
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}

class HandPainter extends CustomPainter {
  final List<double> landmarks;

  HandPainter(this.landmarks);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color.fromARGB(255, 105, 231, 240)
      ..strokeWidth = 4
      ..style = PaintingStyle.fill;

    final linePaint = Paint()
      ..color = Colors.redAccent
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    List<Offset> points = [];
    for (int i = 0; i < landmarks.length; i += 3) {
      double x = landmarks[i]; 
      double y = landmarks[i + 1]; 
      points.add(Offset(x * size.width, y * size.height)); 
    }
    _drawFinger(canvas, linePaint, points, [0, 1, 2, 3, 4]);
    _drawFinger(canvas, linePaint, points, [0, 5, 6, 7, 8]);
    _drawFinger(canvas, linePaint, points, [0, 9, 10, 11, 12]);
    _drawFinger(canvas, linePaint, points, [0, 13, 14, 15, 16]);
    _drawFinger(canvas, linePaint, points, [0, 17, 18, 19, 20]);
    _drawFinger(canvas, linePaint, points, [5, 9, 13, 17, 0]);

    for (var point in points) {
      canvas.drawCircle(point, 3, paint);
    }
  }

  void _drawFinger(Canvas canvas, Paint paint, List<Offset> points, List<int> indices) {
    for (int i = 0; i < indices.length - 1; i++) {
      if (indices[i] < points.length && indices[i+1] < points.length) {
         canvas.drawLine(points[indices[i]], points[indices[i + 1]], paint); 
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true; 
  }
}