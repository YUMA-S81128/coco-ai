import 'package:app/constants/app_assets.dart';
import 'package:app/models/app_state.dart';
import 'package:app/models/job.dart';
import 'package:app/providers/app_state_provider.dart';
import 'package:app/services/storage_service.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// アプリケーションのメイン画面
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appNotifier = ref.read(appStateProvider.notifier);

    // エラー時にSnackBarを表示
    ref.listen(appStateProvider, (previous, next) {
      if (next.status == AppStatus.error && next.errorMessage != null) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(next.errorMessage!)));
      }
    });

    return Scaffold(
      backgroundColor: Colors.lightBlue[50],
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          // リフレッシュボタン
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.black54),
            onPressed: () => appNotifier.reset(),
            tooltip: '新しい質問をはじめる',
          ),
        ],
      ),
      body: const _HomeContent(), // メインコンテンツをステートフルウィジェットに
    );
  }
}

/// メインコンテンツとインタラクションを管理するステートフルウィジェット
class _HomeContent extends ConsumerStatefulWidget {
  const _HomeContent();

  @override
  ConsumerState<_HomeContent> createState() => _HomeContentState();
}

class _HomeContentState extends ConsumerState<_HomeContent> {
  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isAudioPlaying = false;

  @override
  void initState() {
    super.initState();
    // 音声プレーヤーの状態変化をリッスン
    _audioPlayer.onPlayerStateChanged.listen((state) {
      if (mounted) {
        setState(() {
          _isAudioPlaying = state == PlayerState.playing;
        });
      }
    });
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }

  /// 音声再生をトグルする
  Future<void> _toggleAudioPlayback(String audioGcsPath) async {
    if (_isAudioPlaying) {
      await _audioPlayer.stop();
      return;
    }

    try {
      // GCSパスからダウンロードURLを取得
      final url = await ref
          .read(storageServiceProvider)
          .getDownloadUrlFromGsPath(audioGcsPath);
      if (url.isNotEmpty) {
        await _audioPlayer.play(UrlSource(url));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('音声の再生に失敗しました: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final appState = ref.watch(appStateProvider);
    final appNotifier = ref.read(appStateProvider.notifier);

    return Stack(
      children: [
        // 会話コンテンツ
        _buildConversationContent(appState),

        // マイクボタン
        Align(
          alignment: Alignment.bottomCenter,
          child: Padding(
            padding: const EdgeInsets.only(bottom: 40.0),
            child: _buildMicButton(appState, appNotifier),
          ),
        ),
      ],
    );
  }

  /// 会話形式のコンテンツをビルドする
  Widget _buildConversationContent(AppState appState) {
    final job = appState.job;
    final status = appState.status;

    // 初期状態または録音中
    if (status == AppStatus.initial || status == AppStatus.recording) {
      return const Center(
        child: Text(
          'マイクのボタンをおして\n「なんで？」ってきいてみてね！',
          style: TextStyle(fontSize: 18, color: Colors.black54),
          textAlign: TextAlign.center,
        ),
      );
    }

    // 処理中（スピナー表示）
    if (status == AppStatus.processing && job == null) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 24),
            Text('ココとアイが考えてるよ...', style: TextStyle(fontSize: 18)),
          ],
        ),
      );
    }

    // 結果表示
    return Padding(
      padding: const EdgeInsets.only(bottom: 150), // マイクボタンとの重なりを避ける
      child: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        children: [
          // ユーザーの質問（書き起こし）
          if (job?.transcribedText != null && job!.transcribedText!.isNotEmpty)
            _buildChatBubble(
              text: job.transcribedText!,
              character: Character.coco,
            ),

          // AIの回答（説明文）
          if (job?.childExplanation != null && job!.childExplanation!.isNotEmpty)
            _buildChatBubble(
              text: job.childExplanation!,
              character: Character.ai,
            ),

          // 生成された画像
          if (job?.imageGcsPath != null && job!.imageGcsPath!.isNotEmpty)
            _buildImage(job!.imageGcsPath!),

          // ナレーターの音声再生ボタン
          if (job?.finalAudioGcsPath != null &&
              job!.finalAudioGcsPath!.isNotEmpty)
            _buildAudioPlayer(job!.finalAudioGcsPath!),

          // 処理中のインジケーター
          if (status == AppStatus.processing)
            const Padding(
              padding: EdgeInsets.only(top: 20),
              child: Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
    );
  }

  /// マイクボタンをビルドする
  Widget _buildMicButton(AppState appState, AppStateNotifier appNotifier) {
    final isRecording = appState.status == AppStatus.recording;
    final isProcessing = appState.status == AppStatus.processing;

    return IconButton(
      onPressed: isProcessing
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

  /// キャラクターごとのチャット吹き出しをビルドする
  Widget _buildChatBubble({
    required String text,
    required Character character,
  }) {
    final isCoco = character == Character.coco;
    final alignment = isCoco ? Alignment.centerLeft : Alignment.centerRight;
    final crossAxisAlignment = isCoco ? CrossAxisAlignment.start : CrossAxisAlignment.end;
    final avatar = Image.asset(isCoco ? AppAssets.coco : AppAssets.ai, width: 50);
    final bubbleColor = isCoco ? Colors.white : Colors.blue[100];

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: isCoco ? MainAxisAlignment.start : MainAxisAlignment.end,
        children: [
          if (isCoco) ...[avatar, const SizedBox(width: 12)],
          Flexible(
            child: Column(
              crossAxisAlignment: crossAxisAlignment,
              children: [
                Text(isCoco ? 'ココ' : 'アイ', style: const TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: bubbleColor,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(text, style: const TextStyle(fontSize: 16)),
                ),
              ],
            ),
          ),
          if (!isCoco) ...[const SizedBox(width: 12), avatar],
        ],
      ),
    );
  }

  /// 生成された画像ウィジェットをビルドする
  Widget _buildImage(String imageGcsPath) {
    return FutureBuilder<String>(
      future: ref.read(storageServiceProvider).getDownloadUrlFromGsPath(imageGcsPath),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError || !snapshot.hasData || snapshot.data!.isEmpty) {
          return const SizedBox.shrink(); // エラー時は何も表示しない
        }
        final downloadUrl = snapshot.data!;
        return Center(
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 16),
            width: 300,
            height: 300,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              image: DecorationImage(image: NetworkImage(downloadUrl), fit: BoxFit.cover),
              boxShadow: [BoxShadow(color: Colors.black.withAlpha(26), blurRadius: 10)],
            ),
          ),
        );
      },
    );
  }

  /// 音声再生ウィジェットをビルドする
  Widget _buildAudioPlayer(String audioGcsPath) {
    return Center(
      child: Column(
        children: [
          const SizedBox(height: 20),
          ElevatedButton.icon(
            onPressed: () => _toggleAudioPlayback(audioGcsPath),
            icon: Icon(_isAudioPlaying ? Icons.graphic_eq : Icons.play_arrow),
            label: Text(_isAudioPlaying ? 'とめる' : 'アイのおはなしをきく'),
            style: ElevatedButton.styleFrom(
              foregroundColor: Colors.white,
              backgroundColor: Colors.teal,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
            ),
          ),
        ],
      ),
    );
  }
}

enum Character { coco, ai }