import 'package:freezed_annotation/freezed_annotation.dart';

part 'signed_url_response.freezed.dart';
part 'signed_url_response.g.dart';

/// `generate_signed_url` Cloud Functionからのレスポンスを表すクラス
@freezed
abstract class SignedUrlResponse with _$SignedUrlResponse {
  const factory SignedUrlResponse({
    /// 新しく作成されたジョブの一意のID
    required String jobId,

    /// ファイルをアップロードするための署名付きURL
    required String signedUrl,

    /// URLの有効期限（秒）
    required int expiresIn,

    /// アップロードリクエストに含める必要があるHTTPヘッダー
    required Map<String, String> requiredHeaders,
  }) = _SignedUrlResponse;

  /// JSONから`SignedUrlResponse`インスタンスを生成するファクトリコンストラクタ
  factory SignedUrlResponse.fromJson(Map<String, dynamic> json) =>
      _$SignedUrlResponseFromJson(json);
}
