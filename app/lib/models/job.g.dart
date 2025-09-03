// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'job.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_Job _$JobFromJson(Map<String, dynamic> json) => _Job(
  userId: json['userId'] as String?,
  status: $enumDecode(
    _$JobStatusEnumMap,
    json['status'],
    unknownValue: JobStatus.unknown,
  ),
  transcribedText: json['transcribedText'] as String?,
  childExplanation: json['childExplanation'] as String?,
  parentHint: json['parentHint'] as String?,
  illustrationPrompt: json['illustrationPrompt'] as String?,
  imageGcsPath: json['imageGcsPath'] as String?,
  finalAudioGcsPath: json['finalAudioGcsPath'] as String?,
  errorMessage: json['errorMessage'] as String?,
);

Map<String, dynamic> _$JobToJson(_Job instance) => <String, dynamic>{
  'userId': instance.userId,
  'status': _$JobStatusEnumMap[instance.status]!,
  'transcribedText': instance.transcribedText,
  'childExplanation': instance.childExplanation,
  'parentHint': instance.parentHint,
  'illustrationPrompt': instance.illustrationPrompt,
  'imageGcsPath': instance.imageGcsPath,
  'finalAudioGcsPath': instance.finalAudioGcsPath,
  'errorMessage': instance.errorMessage,
};

const _$JobStatusEnumMap = {
  JobStatus.initializing: 'initializing',
  JobStatus.transcribing: 'transcribing',
  JobStatus.explaining: 'explaining',
  JobStatus.illustrating: 'illustrating',
  JobStatus.narrating: 'narrating',
  JobStatus.finishing: 'finishing',
  JobStatus.completed: 'completed',
  JobStatus.error: 'error',
  JobStatus.unknown: 'unknown',
};
