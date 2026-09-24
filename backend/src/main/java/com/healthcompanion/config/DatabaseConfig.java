package com.healthcompanion.config;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import javax.sql.DataSource;
import java.net.URI;

/**
 * Intelligent DataSource configuration supporting:
 * 1. Standard PostgreSQL / MySQL JDBC URLs (via spring.datasource.url or DB_URL)
 * 2. Cloud deployment DATABASE_URL (Render, Railway, Neon, Supabase) in postgres:// or postgresql:// format
 */
@Configuration
public class DatabaseConfig {

    @Value("${spring.datasource.url:}")
    private String datasourceUrl;

    @Value("${spring.datasource.username:}")
    private String username;

    @Value("${spring.datasource.password:}")
    private String password;

    @Bean
    @Primary
    public DataSource dataSource() {
        String envDatabaseUrl = System.getenv("DATABASE_URL");
        String finalUrl = datasourceUrl;
        String finalUsername = username;
        String finalPassword = password;

        if (envDatabaseUrl != null && !envDatabaseUrl.isBlank()) {
            if (envDatabaseUrl.startsWith("postgres://") || envDatabaseUrl.startsWith("postgresql://")) {
                try {
                    String httpFormat = envDatabaseUrl.replaceFirst("^postgres(ql)?://", "http://");
                    URI uri = new URI(httpFormat);
                    String host = uri.getHost();
                    int port = uri.getPort() == -1 ? 5432 : uri.getPort();
                    String path = uri.getPath(); // /dbname
                    String query = uri.getQuery(); // e.g. sslmode=require

                    if (uri.getUserInfo() != null) {
                        String[] userParts = uri.getUserInfo().split(":", 2);
                        finalUsername = userParts[0];
                        if (userParts.length > 1) {
                            finalPassword = userParts[1];
                        }
                    }
                    finalUrl = "jdbc:postgresql://" + host + ":" + port + path + (query != null && !query.isBlank() ? "?" + query : "");
                } catch (Exception e) {
                    if (!envDatabaseUrl.startsWith("jdbc:")) {
                        finalUrl = "jdbc:" + envDatabaseUrl;
                    } else {
                        finalUrl = envDatabaseUrl;
                    }
                }
            } else if (envDatabaseUrl.startsWith("jdbc:")) {
                finalUrl = envDatabaseUrl;
            }
        }

        if (finalUrl == null || finalUrl.isBlank()) {
            finalUrl = "jdbc:postgresql://localhost:5432/ai_health_companion";
        }

        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(finalUrl);
        if (finalUsername != null && !finalUsername.isBlank()) {
            config.setUsername(finalUsername);
        }
        if (finalPassword != null && !finalPassword.isBlank()) {
            config.setPassword(finalPassword);
        }
        return new HikariDataSource(config);
    }
}
