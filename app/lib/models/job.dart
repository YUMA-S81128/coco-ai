import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

part 'job.freezed.dart';
part 'job.g.dart';

/// An enum representing the status of a document in the 'jobs' collection in Firestore.
enum JobStatus {
  initializing,
  transcribing,
  explaining,
  illustrating,
  narrating,
  processing, // Used by the illustrator_agent
  completed,
  error,
  unknown, // For unknown statuses
}

/// A class representing a document in the 'jobs' collection in Firestore.
@freezed
abstract class Job with _$Job {
  const factory Job({
    // This field will be added by the backend function.
    String? userId,
    @JsonKey(unknownEnumValue: JobStatus.unknown) required JobStatus status,
    String? transcribedText,
    String? childExplanation,
    String? parentHint,
    String? illustrationPrompt,
    String? imageGcsPath,
    String? finalAudioGcsPath,
    String? errorMessage,
  }) = _Job;

  factory Job.fromFirestore(DocumentSnapshot<Map<String, dynamic>> snapshot) {
    final data = snapshot.data()!;
    return Job.fromJson(data);
  }

  factory Job.fromJson(Map<String, dynamic> json) => _$JobFromJson(json);
}
