import 'package:app/constants/app_assets.dart';
import 'package:app/models/app_state.dart';
import 'package:app/providers/app_state_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// ホーム画面
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});
 
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Riverpodからアプリケーションの状態を監視
    final appState = ref.watch(appStateProvider);
    final appNotifier = ref.read(appStateProvider.notifier);

    // エラーが発生した場合にSnackBarを表示
    ref.listen(appStateProvider, (previous, next) {
      if (next.status == AppStatus.error && next.errorMessage != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(next.errorMessage!)),
        );
      }
    });

    return Scaffold(
      // 子供が安心するような、目に優しい薄い水色を背景色に設定
      backgroundColor: Colors.lightBlue[50],
      body: Stack(
        children: [
          // --- キャラクター ---
          // ココ（左下）
          Align(
            alignment: Alignment.bottomLeft,
            child: Image.asset(
              AppAssets.coco,
              width: 150,
              height: 150,
            ),
          ),
          // アイ（右下）
          Align(
            alignment: Alignment.bottomRight,
            child: Image.asset(
              AppAssets.ai,
              width: 150,
              height: 150,
            ),
          ),

          // --- 中央のコンテンツエリア ---
          Center(
            child: _buildContent(context, appState),
          ),

          // --- マイクボタン ---
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.only(bottom: 40.0),
              child: _buildMicButton(appState, appNotifier),
            ),
          ),
        ],
      ),
    );
  }
}

/// アプリの状態に応じて中央のコンテンツを構築する
Widget _buildContent(BuildContext context, AppState appState) {
  final textTheme = Theme.of(context).textTheme;

  switch (appState.status) {
    case AppStatus.processing:
      return const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 24),
          Text('ココとアイが考えてるよ...', style: TextStyle(fontSize: 18)),
        ],
      );
    case AppStatus.success:
      return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // AIが生成したイラストを表示
          Container(
            width: 300,
            height: 300,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  spreadRadius: 1,
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
              image: appState.imageUrl != null
                  ? DecorationImage(
                      image: NetworkImage(appState.imageUrl!),
                      fit: BoxFit.cover,
                    )
                  : null,
            ),
            child: appState.imageUrl == null
                ? const Center(child: Text('イラストがないみたい'))
                : null,
          ),
          const SizedBox(height: 24),
          // AIによる解説文を表示
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40),
            child: Text(
              appState.resultText ?? 'なにかお話ししてね！',
              style: textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
          ),
        ],
      );
    case AppStatus.initial:
    case AppStatus.recording:
    case AppStatus.error:
    default:
      // 初期状態やエラー時はシンプルなメッセージを表示
      return Text('マイクのボタンをおして\n「なんで？」ってきいてみてね！',
          style: textTheme.headlineSmall, textAlign: TextAlign.center);
  }
}

/// アプリの状態に応じてマイクボタンを構築する
Widget _buildMicButton(AppState appState, AppStateNotifier appNotifier) {
  final isRecording = appState.status == AppStatus.recording;
  final isProcessing = appState.status == AppStatus.processing;

  return IconButton(
    onPressed: isProcessing
        ? null // 処理中はボタンを無効化
        : () => isRecording
            ? appNotifier.stopRecordingAndProcess()
            : appNotifier.startRecording(),
    icon: Icon(isRecording ? Icons.stop : Icons.mic, color: Colors.white),
    iconSize: 60,
    style: IconButton.styleFrom(
      backgroundColor: isRecording ? Colors.red[400] : Colors.pink[300],
      disabledBackgroundColor: Colors.grey,
      padding: const EdgeInsets.all(24),
      shape: const CircleBorder(),
    ),
  );
}
