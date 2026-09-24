package com.healthcompanion.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity @Table(name = "wellness_analyses")
public class WellnessAnalysis {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false) @JoinColumn(name = "user_id", nullable = false) private User user;
    @Column(nullable = false, columnDefinition = "TEXT") private String analysis;
    @Column(nullable = false, length = 40) private String moodTrend;
    @Column(nullable = false, length = 40) private String stressTrend;
    @Column(nullable = false, length = 40) private String sleepTrend;
    @Column(columnDefinition = "TEXT") private String sleepLmJson;
    @Column(columnDefinition = "TEXT") private String mentaJson;
    @Column(nullable = false, updatable = false) private Instant createdAt;
    @PrePersist void onCreate() { createdAt = Instant.now(); }
    public Long getId() { return id; } public User getUser() { return user; } public void setUser(User v) { user = v; }
    public String getAnalysis() { return analysis; } public void setAnalysis(String v) { analysis = v; }
    public String getMoodTrend() { return moodTrend; } public void setMoodTrend(String v) { moodTrend = v; }
    public String getStressTrend() { return stressTrend; } public void setStressTrend(String v) { stressTrend = v; }
    public String getSleepTrend() { return sleepTrend; } public void setSleepTrend(String v) { sleepTrend = v; }
    public String getSleepLmJson() { return sleepLmJson; } public void setSleepLmJson(String v) { sleepLmJson = v; }
    public String getMentaJson() { return mentaJson; } public void setMentaJson(String v) { mentaJson = v; }
    public Instant getCreatedAt() { return createdAt; }
}
