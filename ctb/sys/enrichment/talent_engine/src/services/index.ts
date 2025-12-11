/**
 * Services Index
 * ==============
 * Re-exports all service wrappers for easy importing.
 */

// Types
export {
  ServiceResponse,
  ServiceEndpoint,
  ProfileData,
  EmailPatternData,
  EmailVerificationData,
  ServiceConfig,
} from "./types";

// Proxycurl
export {
  ProxycurlService,
  ProxycurlProfile,
  ProxycurlExperience,
  createProxycurlService,
} from "./proxycurl";

// Hunter.io
export {
  HunterService,
  HunterDomainResponse,
  HunterEmail,
  HunterEmailFinderResponse,
  createHunterService,
} from "./hunter";

// VitaMail
export {
  VitaMailService,
  VitaMailVerifyResponse,
  createVitaMailService,
} from "./vitamail";

// Apollo (FALLBACK ONLY)
export {
  ApolloService,
  ApolloSearchRequest,
  ApolloSearchResponse,
  ApolloPerson,
  ApolloOrganization,
  createApolloService,
} from "./apollo";

// Metrics Generator
export {
  MetricsGenerator,
  MetricsReport,
  ValidationMetrics,
  EmailMetrics,
  SkipMetrics,
  AgentMetrics,
  globalMetricsGenerator,
} from "./MetricsGenerator";

// Failure Router
export {
  FailureRouter,
  FailureRouterConfig,
  FailureStatistics,
  ExecutionContext,
  RepairRequest,
  ResumeJob,
  globalFailureRouter,
} from "./FailureRouter";

// Requeue Service
export {
  RequeueService,
  RequeueServiceConfig,
  RepairResult,
  BatchRepairResult,
  ProcessQueueResult,
  createRequeueService,
} from "./RequeueService";

// Job Queue
export {
  JobQueue,
  JobQueueConfig,
  Job,
  JobType,
  JobStatus,
  JobPriority,
  JobResult,
  JobProcessor,
  ResumeEnrichmentJob,
  BulkRequeueJob,
  ManualRepairJob,
  QueueStats,
  createJobQueue,
} from "./JobQueue";

// Throttle Manager V2
export {
  ThrottleManagerV2,
  ThrottleRule,
  VendorId,
  VendorUsage,
  ThrottleCheckResult,
  ThrottleBlockReason,
  ThrottleManagerV2Config,
  CallEntry,
  globalThrottleManager,
  createThrottleManager,
} from "./ThrottleManagerV2";

// Cost Governor
export {
  CostGovernor,
  CostGovernorConfig,
  SpendRecord,
  SpendCheckResult,
  CompanyBudget,
  BudgetStatus,
  VendorSpendSummary,
  globalCostGovernor,
} from "./CostGovernor";

// Throttle Errors
export {
  ThrottleError,
  RateLimitError,
  CostLimitError,
  BudgetExceededError,
  CircuitBreakerError,
  VendorDisabledError,
  CooldownActiveError,
  CompanyBudgetExceededError,
  createThrottleError,
  isThrottleError,
  isRetryableThrottleError,
  getFailureBayForThrottleError,
} from "./ThrottleError";

// Throttled Agent
export {
  ThrottledAgentBase,
  ThrottledAgentConfig,
  ThrottledExecutionOptions,
  ThrottledExecutionResult,
  withThrottle,
  throttled,
  createThrottledFunction,
  batchWithThrottle,
} from "./ThrottledAgent";
