package com.healthcompanion.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Central, environment-backed application settings. Keeping these here prevents
 * infrastructure and AI-provider details leaking into controllers or features.
 */
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    private final Cors cors = new Cors();
    private final Ai ai = new Ai();
    private final Upload upload = new Upload();

    public Cors getCors() {
        return cors;
    }

    public Ai getAi() {
        return ai;
    }

    public Upload getUpload() {
        return upload;
    }

    public static class Cors {
        private String allowedOrigins = "http://localhost:5173";

        public String getAllowedOrigins() {
            return allowedOrigins;
        }

        public void setAllowedOrigins(String allowedOrigins) {
            this.allowedOrigins = allowedOrigins;
        }
    }

    public static class Ai {
        private String mode = "mock";
        private String providerBaseUrl = "";

        public String getMode() {
            return mode;
        }

        public void setMode(String mode) {
            this.mode = mode;
        }

        public String getProviderBaseUrl() {
            return providerBaseUrl;
        }

        public void setProviderBaseUrl(String providerBaseUrl) {
            this.providerBaseUrl = providerBaseUrl;
        }
    }

    public static class Upload {
        private long maxImageBytes = 8_388_608L;

        public long getMaxImageBytes() {
            return maxImageBytes;
        }

        public void setMaxImageBytes(long maxImageBytes) {
            this.maxImageBytes = maxImageBytes;
        }
    }
}
