import 'package:app/constants/app_assets.dart';
import 'package:app/models/app_state.dart';
import 'package:app/providers/app_state_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// アプリケーションのメイン画面
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Riverpodからアプリケーションの状態を監視
    final appState = ref.watch(appStateProvider);
    final appNotifier = ref.read(appStateProvider.notifier);

    // エラー時にSnackBarを表示するために状態の変化をリッスンする
    ref.listen(appStateProvider, (previous, next) {
      if (next.status == AppStatus.error && next.errorMessage != null) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(next.errorMessage!)));
      }
    });

    return Scaffold(
      backgroundColor: Colors.lightBlue[50],
      body: Stack(
        children: [
          Align(
            alignment: Alignment.bottomLeft,
            child: Image.asset(AppAssets.coco, width: 150, height: 150),
          ),
          Align(
            alignment: Alignment.bottomRight,
            child: Image.asset(AppAssets.ai, width: 150, height: 150),
          ),

          // 中央のコンテンツをビルド
          Center(child: _buildContent(context, appState)),

          // マイクボタンをビルド
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

/// 現在のアプリ状態に基づいて中央のコンテンツウィジェットをビルドする
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
                  color: Colors.black.withAlpha(26),
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
          // AIが生成した解説テキストを表示
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
      // 初期状態、録音中、またはエラー状態ではシンプルなメッセージを表示
      return Text(
        'マイクのボタンをおして\n「なんで？」ってきいてみてね！',
        style: textTheme.headlineSmall,
        textAlign: TextAlign.center,
      );
  }
}

/// 現在のアプリ状態に基づいてマイクボタンをビルドする
Widget _buildMicButton(AppState appState, AppStateNotifier appNotifier) {
  final isRecording = appState.status == AppStatus.recording;
  final isProcessing = appState.status == AppStatus.processing;

  return IconButton(
    onPressed:
        isProcessing // 処理中はボタンを無効化
        ? null
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
