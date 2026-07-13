alter table social_conversation_log drop constraint social_conversation_log_platform_check;
alter table social_conversation_log add constraint social_conversation_log_platform_check
  check (platform in ('telegram', 'instagram', 'instagram_dm', 'instagram_comment'));
