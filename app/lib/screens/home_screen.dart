import 'package:app/constants/app_assets.dart';
import 'package:app/models/app_state.dart';
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
    final appState = ref.watch(appStateProvider);
    final appNotifier = ref.read(appStateProvider.notifier);
    final screenWidth = MediaQuery.of(context).size.width;
    const breakpoint = 600;

    final isProcessing = appState.status == AppStatus.processing;
    final isInitial = appState.status == AppStatus.initial;

    // エラー時にSnackBarを表示
    ref.listen(appStateProvider, (previous, next) {
      if (next.status == AppStatus.error && next.errorMessage != null) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(next.errorMessage!)));
      }
    });

    return Scaffold(
      backgroundColor: Colors.lightBlue[50],
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          // リフレッシュボタン (画面幅に応じて表示を切り替え)
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: screenWidth > breakpoint
                ? TextButton.icon(
                    icon: const Icon(Icons.refresh, color: Colors.black54),
                    label: const Text(
                      'リフレッシュ',
                      style: TextStyle(color: Colors.black54),
                    ),
                    onPressed: (isInitial || isProcessing)
                        ? null
                        : () => appNotifier.reset(),
                    style: TextButton.styleFrom(
                      foregroundColor: Colors.black54,
                    ),
                  )
                : IconButton(
                    icon: const Icon(Icons.refresh, color: Colors.black54),
                    onPressed: (isInitial || isProcessing)
                        ? null
                        : () => appNotifier.reset(),
                    tooltip: '新しい質問をはじめる',
                  ),
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
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('音声の再生に失敗しました: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final appState = ref.watch(appStateProvider);
    final appNotifier = ref.read(appStateProvider.notifier);
    final status = appState.status;

    final conversationContent = _buildConversationContent(appState);

    if (status == AppStatus.initial || status == AppStatus.recording) {
      return LayoutBuilder(
        builder: (context, constraints) {
          // 横長のウィンドウかどうかを判定
          final bool isWide = constraints.maxWidth > constraints.maxHeight;

          if (isWide) {
            // 横長の場合: コンテンツとマイクボタンを横並びに配置
            return Row(
              children: [
                Expanded(child: conversationContent),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: _buildMicButton(appState, appNotifier),
                ),
              ],
            );
          } else {
            // 縦長の場合: コンテンツの上にマイクボタンを重ねて配置
            return Stack(
              children: [
                conversationContent,
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
        },
      );
    } else {
      // それ以外の状態では、コンテンツをそのまま表示
      return conversationContent;
    }
  }

  /// 会話の状態に応じて適切なUIを構築する
  Widget _buildConversationContent(AppState appState) {
    final status = appState.status;

    if (status == AppStatus.initial || status == AppStatus.recording) {
      return _buildInitialOrRecordingUI();
    }

    if (status == AppStatus.processing && appState.job == null) {
      return _buildProcessingUI();
    }

    return _buildResultUI(appState);
  }

  /// テキストウィジェットを構築するヘルパーメソッド
  Widget _buildTextWidget(String text, {bool useNewline = false}) {
    final processedText = useNewline ? text : text.replaceAll('\n', ' ');
    return Text(
      processedText,
      style: const TextStyle(fontSize: 18, color: Colors.black87),
      textAlign: TextAlign.center,
    );
  }

  /// 初期状態または録音中のUIを構築する
  Widget _buildInitialOrRecordingUI() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Image.asset(AppAssets.coco, width: 80),
              const SizedBox(width: 40),
              Image.asset(AppAssets.ai, width: 80),
            ],
          ),
          const SizedBox(height: 24),
          _buildTextWidget('マイクのボタンをおして\n「なんで？」ってきいてみてね！', useNewline: true),
        ],
      ),
    );
  }

  /// 処理中のUIを構築する
  Widget _buildProcessingUI() {
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

  /// 結果表示のUIを構築する
  Widget _buildResultUI(AppState appState) {
    final job = appState.job;
    if (job == null) return const SizedBox.shrink();

    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
      children: [
        if (job.transcribedText != null && job.transcribedText!.isNotEmpty)
          _buildChatBubble(
            text: job.transcribedText!,
            character: Character.coco,
          ),
        if (job.childExplanation != null && job.childExplanation!.isNotEmpty)
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              _buildChatBubble(
                text: job.childExplanation!,
                character: Character.ai,
              ),
              if (job.finalAudioGcsPath != null &&
                  job.finalAudioGcsPath!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 8, right: 62),
                  child: _buildAudioPlayer(job.finalAudioGcsPath!),
                ),
            ],
          ),
        if (job.imageGcsPath != null && job.imageGcsPath!.isNotEmpty)
          _buildImage(job.imageGcsPath!),
        if (appState.status == AppStatus.processing)
          const Padding(
            padding: EdgeInsets.only(top: 20),
            child: Center(child: CircularProgressIndicator()),
          ),
      ],
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
    final crossAxisAlignment = isCoco
        ? CrossAxisAlignment.start
        : CrossAxisAlignment.end;
    final avatar = Image.asset(
      isCoco ? AppAssets.coco : AppAssets.ai,
      width: 50,
    );
    final bubbleColor = isCoco ? Colors.white : Colors.blue[100];

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: isCoco
            ? MainAxisAlignment.start
            : MainAxisAlignment.end,
        children: [
          if (isCoco) ...[avatar, const SizedBox(width: 12)],
          Flexible(
            child: Column(
              crossAxisAlignment: crossAxisAlignment,
              children: [
                Text(
                  isCoco ? 'ココ' : 'アイ',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
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
      future: ref
          .read(storageServiceProvider)
          .getDownloadUrlFromGsPath(imageGcsPath),
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
              image: DecorationImage(
                image: NetworkImage(downloadUrl),
                fit: BoxFit.cover,
              ),
              boxShadow: [
                BoxShadow(color: Colors.black.withAlpha(26), blurRadius: 10),
              ],
            ),
          ),
        );
      },
    );
  }

  /// 音声再生ウィジェットをビルドする
  Widget _buildAudioPlayer(String audioGcsPath) {
    return ElevatedButton.icon(
      onPressed: () => _toggleAudioPlayback(audioGcsPath),
      icon: Icon(_isAudioPlaying ? Icons.graphic_eq : Icons.play_arrow),
      label: Text(_isAudioPlaying ? 'とめる' : 'アイのおはなしをきく'),
      style: ElevatedButton.styleFrom(
        foregroundColor: Colors.white,
        backgroundColor: Colors.teal,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
      ),
    );
  }
}

enum Character { coco, ai }
