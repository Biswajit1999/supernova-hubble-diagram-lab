"use strict";

importScripts("science-core.js");

self.onmessage = (event) => {
  const { runId, points, params } = event.data || {};
  try {
    const result = self.SupernovaScience.analyze(points, params);
    self.postMessage({ runId, result });
  } catch (error) {
    self.postMessage({ runId, error: error instanceof Error ? error.message : String(error) });
  }
};
