-- ============================================================
-- File 13: Seed data for plans, quotas, features, config definitions, platform roles
-- ============================================================
INSERT INTO platform.quota_definitions(quota_key, display_name, unit, reset_period, is_metered) VALUES
('seats','Seats','seat','monthly',true),
('ai_tokens_monthly','AI tokens per month','token','monthly',true),
('voice_minutes_monthly','Voice minutes per month','minute','monthly',true),
('job_postings_monthly','Job postings per month','posting','monthly',true),
('api_calls_monthly','API calls per month','call','monthly',true)
ON CONFLICT (quota_key) DO NOTHING;

INSERT INTO platform.feature_definitions(feature_key, name, category, default_enabled, requires_human_governance) VALUES
('corporate_ats','Corporate ATS','ats',true,false),
('agency_ats','Agency ATS','ats',false,false),
('ai_recruiter','AI Recruiter','ai',false,true),
('ai_interviewer','AI Interviewer','ai',false,true),
('client_portal','Client Portal','agency',false,false),
('public_partner_api','Public Partner API','platform',false,false),
('white_labeling','White Labeling','platform',false,false),
('advanced_analytics','Advanced Analytics','analytics',false,false)
ON CONFLICT (feature_key) DO NOTHING;

INSERT INTO platform.plans(code, name, description, status, billing_interval, base_price, currency, min_seats, max_seats, trial_days) VALUES
('starter','Starter','Starter plan for small teams','active','monthly',0,'USD',1,10,14),
('professional','Professional','Professional ATS plan','active','monthly',299,'USD',5,100,14),
('enterprise','Enterprise','Enterprise contract-backed plan','active','custom',0,'USD',25,NULL,0)
ON CONFLICT (code) DO NOTHING;

INSERT INTO platform.platform_permissions(permission_key, description) VALUES
('platform.tenant.read','Read tenants'),
('platform.tenant.write','Modify tenants'),
('platform.support.impersonate','Start audited support session'),
('platform.billing.read','Read platform billing'),
('platform.governance.write','Manage AI governance')
ON CONFLICT (permission_key) DO NOTHING;
INSERT INTO platform.platform_roles(role_key, name, description) VALUES
('super_admin','Super Admin','Full platform administration'),
('support_admin','Support Admin','Audited support access'),
('ai_governance_admin','AI Governance Admin','Manage AI model/prompt governance')
ON CONFLICT (role_key) DO NOTHING;

INSERT INTO platform.config_definitions(config_key, name, value_type, default_bool, description) VALUES
('ai.human_review.required','Require human review for AI decisions','boolean',true,'Global default for AI decisions to require HITL'),
('security.mfa.required_for_admins','Require MFA for administrators','boolean',true,'MFA policy default'),
('notifications.email.enabled','Enable email notifications','boolean',true,'Controls email notification delivery')
ON CONFLICT (config_key) DO NOTHING;
INSERT INTO platform.config_scope_levels(config_definition_id, scope_level)
SELECT id, 'tenant'::config_scope_enum FROM platform.config_definitions
ON CONFLICT DO NOTHING;

INSERT INTO notif.notification_templates(template_key, category, name) VALUES
('approval_request','transactional','Approval Request'),
('interview_reminder','transactional','Interview Reminder'),
('ai_review_required','ai_alert','AI Review Required'),
('password_reset','transactional','Password Reset'),
('email_verification','transactional','Email Verification')
ON CONFLICT (template_key) DO NOTHING;
INSERT INTO notif.notification_template_channels(template_id, channel)
SELECT id, 'email'::notif_channel_enum FROM notif.notification_templates
ON CONFLICT DO NOTHING;
INSERT INTO analytics.metric_definitions(metric_key, display_name, unit) VALUES
('time_to_fill_days','Time to Fill','days'),
('application_count','Applications','count'),
('candidate_conversion_rate','Candidate Conversion Rate','percent'),
('ai_override_rate','AI Override Rate','percent'),
('placement_fee_revenue','Placement Fee Revenue','currency')
ON CONFLICT(metric_key) DO NOTHING;
INSERT INTO analytics.dimension_definitions(dimension_key, display_name) VALUES
('business_unit','Business Unit'),('requisition','Requisition'),('client','Client'),('source','Source'),('stage','Stage')
ON CONFLICT(dimension_key) DO NOTHING;
