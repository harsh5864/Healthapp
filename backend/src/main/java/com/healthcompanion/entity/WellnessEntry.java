package com.healthcompanion.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity @Table(name = "wellness_entries")
public class WellnessEntry {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false) @JoinColumn(name = "user_id", nullable = false) private User user;
    @Column(nullable = false) private Integer mood;
    @Column(nullable = false) private Integer stress;
    @Column(nullable = false) private Integer energy;
    @Column(nullable = false) private Double sleepHours;
    @Column(nullable = false) private Integer activity = 5;
    @Column(columnDefinition = "TEXT") private String journalText;
    @Column(nullable = false, updatable = false) private Instant createdAt;
    @PrePersist void onCreate() { createdAt = Instant.now(); }
    public Long getId() { return id; } public User getUser() { return user; } public void setUser(User v) { user = v; }
    public Integer getMood() { return mood; } public void setMood(Integer v) { mood = v; }
    public Integer getStress() { return stress; } public void setStress(Integer v) { stress = v; }
    public Integer getEnergy() { return energy; } public void setEnergy(Integer v) { energy = v; }
    public Double getSleepHours() { return sleepHours; } public void setSleepHours(Double v) { sleepHours = v; }
    public Integer getActivity() { return activity != null ? activity : 5; } public void setActivity(Integer v) { activity = v != null ? v : 5; }
    public String getJournalText() { return journalText; } public void setJournalText(String v) { journalText = v; }
    public Instant getCreatedAt() { return createdAt; }
}
