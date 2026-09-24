import { useEffect, useRef, useState } from 'react';
import { foodApi, nutrientApi } from '../services/appServices';

export default function FoodScannerPage() {
  const ref = useRef();
  const [mode, setMode] = useState('REAL_FOOD'); // 'REAL_FOOD', 'PACKED_FOOD', or 'PRODUCE'
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Intake logging state
  const [selectedMealType, setSelectedMealType] = useState('LUNCH');
  const [intakeLogging, setIntakeLogging] = useState(false);
  const [intakeSuccess, setIntakeSuccess] = useState('');

  // 3-Day History state
  const [overview, setOverview] = useState(null);
  const [selectedDayIdx, setSelectedDayIdx] = useState(0); // 0 = Today, 1 = Yesterday, 2 = 2 Days Ago
  const [trackerLoading, setTrackerLoading] = useState(false);

  // Auto-detect meal type based on local time
  useEffect(() => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 11) setSelectedMealType('BREAKFAST');
    else if (hour >= 11 && hour < 16) setSelectedMealType('LUNCH');
    else if (hour >= 16 && hour < 22) setSelectedMealType('DINNER');
    else setSelectedMealType('SNACK');
  }, []);

  const load3DaySummary = async () => {
    try {
      setTrackerLoading(true);
      const res = await nutrientApi.get3DaySummary();
      setOverview(res.data);
    } catch {
      // Quietly fail or keep existing state
    } finally {
      setTrackerLoading(false);
    }
  };

  useEffect(() => {
    load3DaySummary();
  }, []);

  const choose = (f) => {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError('');
    setIntakeSuccess('');
  };

  const clearSelection = () => {
    setFile(null);
    setPreview('');
    setResult(null);
    setError('');
    setIntakeSuccess('');
  };

  const switchMode = (newMode) => {
    if (newMode === mode) return;
    setMode(newMode);
    clearSelection();
  };

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setIntakeSuccess('');
    try {
      const res = await foodApi.analyze(file, mode);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.message || 'We could not analyze that image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogIntake = async () => {
    if (!result) return;
    setIntakeLogging(true);
    setError('');
    try {
      const calories = result.calories ?? (mode === 'PRODUCE' ? 80 : 250);
      const protein = result.protein ?? (mode === 'PRODUCE' ? 1.0 : 5.0);
      const carbs = result.carbs ?? (mode === 'PRODUCE' ? 18.0 : 35.0);
      const fat = result.fat ?? (mode === 'PRODUCE' ? 0.3 : 10.0);
      const fiber = result.fiber ?? (mode === 'PRODUCE' ? 3.0 : 2.0);

      await nutrientApi.log({
        foodName: result.foodName || 'Scanned Food',
        mealType: selectedMealType,
        calories: Math.round(calories),
        protein: Math.round(protein * 10) / 10,
        carbs: Math.round(carbs * 10) / 10,
        fat: Math.round(fat * 10) / 10,
        fiber: Math.round(fiber * 10) / 10,
        portionSize: result.portionSize || '1 standard serving',
      });

      setIntakeSuccess(`✓ Logged ${result.foodName} (${calories} kcal, ${protein}g protein) to today's intake!`);
      await load3DaySummary();
      setSelectedDayIdx(0); // Switch to Today
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to log intake. Please try again.');
    } finally {
      setIntakeLogging(false);
    }
  };

  const handleDeleteIntake = async (id) => {
    try {
      await nutrientApi.remove(id);
      await load3DaySummary();
    } catch {
      // Ignore or notify
    }
  };

  const isRealFood = mode === 'REAL_FOOD';
  const isPacked = mode === 'PACKED_FOOD';
  const isProduce = mode === 'PRODUCE';

  const grade = (result?.grade || 'C').toUpperCase();
  const gradeLower = grade.toLowerCase();

  const extractSection = (text, prefix) => {
    if (!text) return [];
    const lines = text.split('\n\n');
    const target = lines.find((l) => l.toLowerCase().startsWith(prefix.toLowerCase()));
    if (!target) return [];
    const content = target.replace(new RegExp(`^${prefix}:?\\s*`, 'i'), '');
    return content
      .split(';')
      .map((s) => s.trim().replace(/^\*\s*/, '').replace(/\.$/, ''))
      .filter(Boolean);
  };

  const positives = extractSection(result?.observations, 'Key Positives');
  const concerns = extractSection(result?.observations, 'Nutritional Concerns');

  const gradeNames = {
    A: 'Grade A · Best Quality',
    B: 'Grade B · Good / Balanced',
    C: 'Grade C · Moderate / Fair',
    D: 'Grade D · Poor Profile',
    F: 'Grade F · Ultra-Processed',
  };

  // Selected Day in 3-day history
  const activeDay = overview?.history?.[selectedDayIdx] || overview?.today || {
    label: 'Today',
    date: new Date().toISOString().split('T')[0],
    totalCalories: 0,
    totalProtein: 0,
    totalCarbs: 0,
    totalFat: 0,
    totalFiber: 0,
    items: [],
  };

  const calorieTarget = overview?.dailyCalorieTarget || 2000;
  const calPercent = Math.min(100, Math.round((activeDay.totalCalories / calorieTarget) * 100));

  const proteinTarget = overview?.dailyProteinTarget || 60;
  const carbsTarget = overview?.dailyCarbsTarget || 250;
  const fatTarget = overview?.dailyFatTarget || 70;
  const fiberTarget = overview?.dailyFiberTarget || 30;

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <p className="eyebrow">🍎 Smart Food & Nutrient Intake Scanner</p>
          <h1>Scan what you eat.</h1>
          <p>
            {isRealFood
              ? 'Snap a photo of your meal or plate. Google Gemma 4 26B calculates your calories, protein, carbs, and fat — ready to log into your daily nutrient intake.'
              : isPacked
              ? 'Photograph food ingredients or packaging to get an instant nutritional health grade (A to F) powered by Google Gemma 4 26B.'
              : 'Upload a fruit or vegetable photo for an AI-assisted visible freshness and condition check.'}
          </p>
        </div>
      </div>

      {/* Mode Selector Tabs */}
      <div className="scanner-tabs scanner-tabs--three">
        <button
          type="button"
          className={`scanner-tab ${isRealFood ? 'active' : ''}`}
          onClick={() => switchMode('REAL_FOOD')}
        >
          <span>🍲</span> Real Food & Meal Intake
        </button>
        <button
          type="button"
          className={`scanner-tab ${isPacked ? 'active' : ''}`}
          onClick={() => switchMode('PACKED_FOOD')}
        >
          <span>📦</span> Packaged Food & Grade
        </button>
        <button
          type="button"
          className={`scanner-tab ${isProduce ? 'active' : ''}`}
          onClick={() => switchMode('PRODUCE')}
        >
          <span>🍎</span> Fresh Produce
        </button>
      </div>

      <div className="scanner-layout">
        {/* Upload Column */}
        <div className="upload-card">
          <input
            ref={ref}
            hidden
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={(e) => choose(e.target.files[0])}
          />
          {preview ? (
            <div className="image-preview">
              <img src={preview} alt="Selected food preview" />
              <button type="button" onClick={clearSelection}>
                Remove
              </button>
            </div>
          ) : (
            <button type="button" className="drop-zone" onClick={() => ref.current?.click()}>
              <span>{isRealFood ? '🍲' : isPacked ? '📦' : '🍎'}</span>
              <b>
                {isRealFood
                  ? 'Photograph your cooked meal or plate'
                  : isPacked
                  ? 'Photograph food packet or ingredients'
                  : 'Choose a produce photo'}
              </b>
              <small>
                {isRealFood
                  ? 'Plate, bowl, home-cooked dish, or takeout · camera supported'
                  : isPacked
                  ? 'Ingredient label, nutrition facts, or front package · camera supported'
                  : 'JPG, PNG or WebP · max 8 MB · camera supported'}
              </small>
            </button>
          )}

          <button
            type="button"
            className="button button--primary full"
            disabled={!file || loading}
            onClick={analyze}
          >
            {loading
              ? isRealFood
                ? 'Calculating nutrients with Gemma 4 26B…'
                : isPacked
                ? 'Grading ingredients with Gemma 4 26B…'
                : 'Analyzing produce condition…'
              : isRealFood
              ? 'Calculate Nutrients & Intake'
              : isPacked
              ? 'Analyze Nutritional Grade (A–F)'
              : 'Analyze Freshness Condition'}
          </button>

          {error && <div className="form-error">{error}</div>}
        </div>

        {/* Results Column */}
        {result ? (
          <div className="result-card">
            {/* === 1. REAL FOOD / MEAL INTAKE RESULT === */}
            {isRealFood && (
              <>
                <div className="grade-display-box" style={{ background: '#f5faf7' }}>
                  <div className="grade-details">
                    <span className="result-label">Detected Meal & Portion</span>
                    <h2 className="grade-title">{result.foodName}</h2>
                    <span className="processing-tag processing-tag--nova1">
                      {result.portionSize || '1 standard portion'} · {result.condition || 'Nutrient-Dense Meal'}
                    </span>
                  </div>
                  <div className="score" style={{ flexShrink: 0 }}>
                    <strong>{result.freshnessScore ?? 85}</strong>
                    <small>/100 Health</small>
                  </div>
                </div>

                {/* Macronutrient Cards */}
                <div className="macro-grid">
                  <div className="macro-card macro-card--cal">
                    <span className="macro-icon">🔥</span>
                    <span className="macro-val">{result.calories ?? 0}</span>
                    <span className="macro-unit">kcal</span>
                    <div className="macro-label">Calories</div>
                  </div>
                  <div className="macro-card macro-card--pro">
                    <span className="macro-icon">🥩</span>
                    <span className="macro-val">{result.protein ?? 0}</span>
                    <span className="macro-unit">g</span>
                    <div className="macro-label">Protein</div>
                  </div>
                  <div className="macro-card macro-card--carb">
                    <span className="macro-icon">🍞</span>
                    <span className="macro-val">{result.carbs ?? 0}</span>
                    <span className="macro-unit">g</span>
                    <div className="macro-label">Carbs</div>
                  </div>
                  <div className="macro-card macro-card--fat">
                    <span className="macro-icon">🥑</span>
                    <span className="macro-val">{result.fat ?? 0}</span>
                    <span className="macro-unit">g</span>
                    <div className="macro-label">Fat</div>
                  </div>
                  <div className="macro-card macro-card--fib">
                    <span className="macro-icon">🌾</span>
                    <span className="macro-val">{result.fiber ?? 0}</span>
                    <span className="macro-unit">g</span>
                    <div className="macro-label">Fiber</div>
                  </div>
                </div>

                <div className="result-block">
                  <b>Nutritional Observations</b>
                  <p style={{ whiteSpace: 'pre-line' }}>{result.observations}</p>
                </div>

                <div className="result-block">
                  <b>Dietary Fit & Recommendation</b>
                  <p>{result.recommendation}</p>
                </div>

                {/* Bottom Confirmation Box: "Is this your intake?" */}
                <div className="intake-prompt-card">
                  <div className="intake-prompt-header">
                    <div className="intake-prompt-icon">🍽️</div>
                    <div>
                      <h3 className="intake-prompt-title">Is this your intake?</h3>
                      <p className="intake-prompt-sub">
                        If you ate this food, log it now to automatically calculate it in your daily nutrient intake and 3-day history.
                      </p>
                    </div>
                  </div>

                  <div className="meal-type-selector">
                    <button
                      type="button"
                      className={`meal-type-btn ${selectedMealType === 'BREAKFAST' ? 'active' : ''}`}
                      onClick={() => setSelectedMealType('BREAKFAST')}
                    >
                      🌅 Breakfast
                    </button>
                    <button
                      type="button"
                      className={`meal-type-btn ${selectedMealType === 'LUNCH' ? 'active' : ''}`}
                      onClick={() => setSelectedMealType('LUNCH')}
                    >
                      ☀️ Lunch
                    </button>
                    <button
                      type="button"
                      className={`meal-type-btn ${selectedMealType === 'DINNER' ? 'active' : ''}`}
                      onClick={() => setSelectedMealType('DINNER')}
                    >
                      🌙 Dinner
                    </button>
                    <button
                      type="button"
                      className={`meal-type-btn ${selectedMealType === 'SNACK' ? 'active' : ''}`}
                      onClick={() => setSelectedMealType('SNACK')}
                    >
                      🍎 Snack
                    </button>
                  </div>

                  <div className="intake-action-row">
                    <button
                      type="button"
                      className="intake-log-btn"
                      disabled={intakeLogging}
                      onClick={handleLogIntake}
                    >
                      {intakeLogging ? 'Saving to Tracker…' : '✓ Yes, Log This To My Daily Intake'}
                    </button>
                  </div>

                  {intakeSuccess && (
                    <div className="intake-success-badge" style={{ marginTop: '12px' }}>
                      <span>🎉</span> {intakeSuccess}
                    </div>
                  )}
                </div>

                <div>
                  <span className="ai-attribution-pill">
                    ✦ Powered by Google Gemma 4 26B A4B
                  </span>
                </div>
              </>
            )}

            {/* === 2. PACKED FOOD / GRADE RESULT === */}
            {isPacked && (
              <>
                <div className="grade-display-box">
                  <div className="grade-details">
                    <span className="result-label">Analyzed Packaged Item</span>
                    <h2 className="grade-title">{result.foodName}</h2>
                    <span className={`processing-tag processing-tag--nova${grade === 'A' ? '1' : grade === 'B' ? '2' : grade === 'C' ? '3' : '4'}`}>
                      {result.condition || gradeNames[grade] || `Grade ${grade}`}
                    </span>
                  </div>

                  <div className={`grade-badge-huge grade-badge-huge--${['a', 'b', 'c', 'd', 'f'].includes(gradeLower) ? gradeLower : 'c'}`}>
                    <span>{grade}</span>
                    <small>Grade</small>
                  </div>
                </div>

                <div className="nutri-scale" aria-label="Nutri-Grade Scale">
                  <div className={`nutri-scale-step step-a ${grade === 'A' ? 'active' : ''}`}>A</div>
                  <div className={`nutri-scale-step step-b ${grade === 'B' ? 'active' : ''}`}>B</div>
                  <div className={`nutri-scale-step step-c ${grade === 'C' ? 'active' : ''}`}>C</div>
                  <div className={`nutri-scale-step step-d ${grade === 'D' ? 'active' : ''}`}>D</div>
                  <div className={`nutri-scale-step step-f ${grade === 'F' ? 'active' : ''}`}>F</div>
                </div>

                <div className="result-block">
                  <b>Health Score & Quality Score</b>
                  <p>
                    Nutritional Health Rating: <strong>{result.freshnessScore} / 100</strong>{' '}
                    <span style={{ color: '#7a968d' }}>
                      ({grade === 'A' ? 'Best / Highly Recommended' : grade === 'B' ? 'Wholesome & Balanced' : grade === 'C' ? 'Moderate Quality' : grade === 'D' ? 'Poor Nutritional Value' : 'Ultra-Processed / Avoid'})
                    </span>
                  </p>
                </div>

                <div className="bullet-grid">
                  {positives.length > 0 && (
                    <div className="bullet-card bullet-card--pos">
                      <b>✓ Clean & Beneficial Ingredients</b>
                      <ul>
                        {positives.map((p, idx) => (
                          <li key={idx}>{p}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {concerns.length > 0 && (
                    <div className="bullet-card bullet-card--neg">
                      <b>⚠ Additives & Concerns Flagged</b>
                      <ul>
                        {concerns.map((c, idx) => (
                          <li key={idx}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="result-block" style={{ marginTop: '18px' }}>
                  <b>Ingredient Analysis & Verdict</b>
                  <p style={{ whiteSpace: 'pre-line' }}>{result.observations}</p>
                </div>

                <div className="result-block">
                  <b>Smart Swap & Health Recommendation</b>
                  <p>{result.recommendation}</p>
                </div>

                {/* Optional Intake Log for Packed Food */}
                <div className="intake-prompt-card">
                  <div className="intake-prompt-header">
                    <div className="intake-prompt-icon">🍽️</div>
                    <div>
                      <h3 className="intake-prompt-title">Did you consume this snack or food?</h3>
                      <p className="intake-prompt-sub">Add this packaged item to your daily intake log.</p>
                    </div>
                  </div>
                  <div className="intake-action-row">
                    <button
                      type="button"
                      className="intake-log-btn"
                      disabled={intakeLogging}
                      onClick={handleLogIntake}
                    >
                      {intakeLogging ? 'Saving…' : '✓ Yes, Log This Intake'}
                    </button>
                  </div>
                  {intakeSuccess && (
                    <div className="intake-success-badge" style={{ marginTop: '12px' }}>
                      <span>🎉</span> {intakeSuccess}
                    </div>
                  )}
                </div>

                <div>
                  <span className="ai-attribution-pill">
                    ✦ Evaluated by Google Gemma 4 26B A4B
                  </span>
                </div>
              </>
            )}

            {/* === 3. FRESH PRODUCE RESULT === */}
            {isProduce && (
              <>
                <div className="result-top">
                  <div>
                    <span className="result-label">Detected Produce</span>
                    <h2>{result.foodName}</h2>
                  </div>
                  <div className="score">
                    <strong>{result.freshnessScore}</strong>
                    <small>/100</small>
                  </div>
                </div>
                <span className="condition-pill">{result.condition}</span>
                <div className="result-block">
                  <b>Visible observations</b>
                  <p>{result.observations}</p>
                </div>
                <div className="result-block">
                  <b>Recommendation</b>
                  <p>{result.recommendation}</p>
                </div>

                {/* Optional Produce Intake Log */}
                <div className="intake-prompt-card">
                  <div className="intake-prompt-header">
                    <div className="intake-prompt-icon">🍎</div>
                    <div>
                      <h3 className="intake-prompt-title">Did you eat this fruit or vegetable?</h3>
                      <p className="intake-prompt-sub">Add this fresh produce to your daily nutrient tracker.</p>
                    </div>
                  </div>
                  <div className="intake-action-row">
                    <button
                      type="button"
                      className="intake-log-btn"
                      disabled={intakeLogging}
                      onClick={handleLogIntake}
                    >
                      {intakeLogging ? 'Saving…' : '✓ Yes, Log Produce Intake'}
                    </button>
                  </div>
                  {intakeSuccess && (
                    <div className="intake-success-badge" style={{ marginTop: '12px' }}>
                      <span>🎉</span> {intakeSuccess}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        ) : (
          /* Info Placeholder Column */
          <div className="scanner-info">
            <span>✦</span>
            <h2>
              {isRealFood
                ? 'Cooked Meals & Nutrient Breakdown'
                : isPacked
                ? 'Grade A to F Nutritional Quality'
                : 'Visible condition checks'}
            </h2>
            <p>
              {isRealFood
                ? 'Take a photo of your plate, homemade meal, or restaurant dish. Google Gemma 4 26B identifies individual ingredients, visual portions, and provides realistic caloric and macronutrient numbers (Protein, Carbs, Fat, Fiber).'
                : isPacked
                ? 'Our Gemma 4 26B A4B vision model reads the ingredients list, identifies preservatives, added sugars, harmful dyes, and processing levels to classify the food from Grade A (Clean & wholesome) to Grade F (Ultra-processed).'
                : 'This tool evaluates visible characteristics such as coloration, skin firmness, bruising, and surface decay. Always inspect produce yourself before preparing.'}
            </p>
          </div>
        )}
      </div>

      {/* ========================================================
          3-DAY NUTRIENT INTAKE TRACKER DASHBOARD
          ======================================================== */}
      <div className="nutrient-tracker-section">
        <div className="nutrient-tracker-header">
          <div className="nutrient-tracker-title">
            <p className="eyebrow" style={{ marginBottom: '4px' }}>📈 Calorie & Macro History</p>
            <h2>3-Day Nutrient Intake Tracker</h2>
            <p>Review and monitor your daily calorie and macronutrient balance across a rolling 3-day history.</p>
          </div>

          <div className="history-day-tabs">
            {overview?.history?.map((day, idx) => (
              <button
                key={day.date}
                type="button"
                className={`history-day-tab ${selectedDayIdx === idx ? 'active' : ''}`}
                onClick={() => setSelectedDayIdx(idx)}
              >
                {day.label} ({new Date(day.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })})
              </button>
            )) || (
              <button type="button" className="history-day-tab active">
                Today
              </button>
            )}
          </div>
        </div>

        <div className="tracker-grid">
          {/* Day Totals & Macro Progress */}
          <div className="day-totals-card">
            <div className="day-totals-header">
              <span className="day-totals-title">{activeDay.label} Overview</span>
              <span className="day-totals-date">{activeDay.date}</span>
            </div>

            {/* Calorie Bar */}
            <div className="calorie-progress-box">
              <div className="calorie-meta">
                <span className="calorie-current">{activeDay.totalCalories} kcal</span>
                <span className="calorie-target">Target: {calorieTarget} kcal ({calPercent}%)</span>
              </div>
              <div className="calorie-bar-bg">
                <div className="calorie-bar-fill" style={{ width: `${calPercent}%` }} />
              </div>
            </div>

            {/* Macro Bars */}
            <div className="macro-progress-list">
              <div className="macro-progress-item">
                <div className="macro-progress-info">
                  <span>🥩 Protein</span>
                  <span>{activeDay.totalProtein}g / {proteinTarget}g</span>
                </div>
                <div className="macro-bar-bg">
                  <div
                    className="macro-bar-fill macro-bar-fill--pro"
                    style={{ width: `${Math.min(100, Math.round((activeDay.totalProtein / proteinTarget) * 100))}%` }}
                  />
                </div>
              </div>

              <div className="macro-progress-item">
                <div className="macro-progress-info">
                  <span>🍞 Carbohydrates</span>
                  <span>{activeDay.totalCarbs}g / {carbsTarget}g</span>
                </div>
                <div className="macro-bar-bg">
                  <div
                    className="macro-bar-fill macro-bar-fill--carb"
                    style={{ width: `${Math.min(100, Math.round((activeDay.totalCarbs / carbsTarget) * 100))}%` }}
                  />
                </div>
              </div>

              <div className="macro-progress-item">
                <div className="macro-progress-info">
                  <span>🥑 Total Fat</span>
                  <span>{activeDay.totalFat}g / {fatTarget}g</span>
                </div>
                <div className="macro-bar-bg">
                  <div
                    className="macro-bar-fill macro-bar-fill--fat"
                    style={{ width: `${Math.min(100, Math.round((activeDay.totalFat / fatTarget) * 100))}%` }}
                  />
                </div>
              </div>

              <div className="macro-progress-item">
                <div className="macro-progress-info">
                  <span>🌾 Dietary Fiber</span>
                  <span>{activeDay.totalFiber}g / {fiberTarget}g</span>
                </div>
                <div className="macro-bar-bg">
                  <div
                    className="macro-bar-fill macro-bar-fill--fib"
                    style={{ width: `${Math.min(100, Math.round((activeDay.totalFiber / fiberTarget) * 100))}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Logged Meals List */}
          <div className="day-meals-card">
            <div className="day-meals-title">
              <span>Meals Logged for {activeDay.label}</span>
              <small style={{ color: '#769188', fontWeight: 600 }}>{activeDay.items?.length || 0} item(s)</small>
            </div>

            {activeDay.items && activeDay.items.length > 0 ? (
              <div className="day-meals-list">
                {activeDay.items.map((meal) => (
                  <div key={meal.id} className="meal-item-row">
                    <div className="meal-item-main">
                      <div className="meal-item-tags">
                        <span className={`meal-badge meal-badge--${meal.mealType}`}>
                          {meal.mealType}
                        </span>
                        {meal.createdAt && (
                          <span className="meal-item-time">
                            {new Date(meal.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        )}
                      </div>
                      <h4 className="meal-item-name">{meal.foodName}</h4>
                      {meal.portionSize && <span className="meal-item-portion">{meal.portionSize}</span>}
                    </div>

                    <div className="meal-item-stats">
                      <div className="meal-item-cals">{meal.calories} kcal</div>
                      <div className="meal-item-macros">
                        P: {meal.protein}g · C: {meal.carbs}g · F: {meal.fat}g
                      </div>
                    </div>

                    <button
                      type="button"
                      className="meal-item-delete"
                      title="Remove meal from intake"
                      onClick={() => handleDeleteIntake(meal.id)}
                    >
                      &times;
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-day-state">
                <span>🍽️</span>
                <b>No meals logged for this day yet</b>
                <p>Take a picture of your food above and click "Log to My Daily Intake" to start tracking!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
