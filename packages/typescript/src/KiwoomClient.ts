import { callKiwoom, KiwoomResponse } from "./client.js";
import { API_PATHS, API_SEGMENTS } from "./generated/api_paths.js";

export class SegmentClient {
  constructor(private readonly _segment: string) {}

  call(apiId: string, args: Record<string, unknown> = {}): Promise<KiwoomResponse> {
    const realPath = API_PATHS[apiId];
    if (!realPath) throw new Error(`Unknown api_id: ${apiId}`);
    if (API_SEGMENTS[apiId] !== this._segment) {
      throw new Error(
        `api_id ${apiId} belongs to segment '${API_SEGMENTS[apiId]}', not '${this._segment}'`
      );
    }
    return callKiwoom(realPath, apiId, args);
  }
}

export interface KiwoomClientConfig {
  appKey?: string;
  appSecret?: string;
  env?: "live" | "mock";
  accessToken?: string;
}

export class KiwoomClient {
  readonly acnt = new SegmentClient("acnt");
  readonly chart = new SegmentClient("chart");
  readonly crdordr = new SegmentClient("crdordr");
  readonly elw = new SegmentClient("elw");
  readonly etf = new SegmentClient("etf");
  readonly frgnistt = new SegmentClient("frgnistt");
  readonly mrkcond = new SegmentClient("mrkcond");
  readonly ordr = new SegmentClient("ordr");
  readonly rkinfo = new SegmentClient("rkinfo");
  readonly sect = new SegmentClient("sect");
  readonly shsa = new SegmentClient("shsa");
  readonly slb = new SegmentClient("slb");
  readonly stkinfo = new SegmentClient("stkinfo");
  readonly thme = new SegmentClient("thme");

  constructor(config: KiwoomClientConfig = {}) {
    if (config.appKey) process.env.KIWOOM_APP_KEY = config.appKey;
    if (config.appSecret) process.env.KIWOOM_APP_SECRET = config.appSecret;
    if (config.env) process.env.KIWOOM_ENV = config.env;
    if (config.accessToken) process.env.KIWOOM_ACCESS_TOKEN = config.accessToken;
  }

  call(apiId: string, args: Record<string, unknown> = {}): Promise<KiwoomResponse> {
    const realPath = API_PATHS[apiId];
    if (!realPath) throw new Error(`Unknown api_id: ${apiId}`);
    return callKiwoom(realPath, apiId, args);
  }
}
