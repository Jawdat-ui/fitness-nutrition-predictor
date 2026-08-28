"""Fitness & Nutrition Predictor — Streamlit Web App (v2).

A flashy, modern web interface with AI assistant integration.

Launch with:
    streamlit run app.py
"""

from __future__ import annotations

import os
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from fitness_predictor.models import (
    ActivityLevel, Goal, LiftLog, MacroTarget, NutritionLog,
    Sex, StrengthLevel, UserProfile, WeightUnit, LB_PER_KG,
)
from fitness_predictor.prediction.calorie_model import calculate_macro_targets
from fitness_predictor.prediction.one_rep_max import calculate_1rm
from fitness_predictor.prediction.rep_percentage import (
    REP_PERCENTAGES, suggested_working_weight,
)
from fitness_predictor.prediction.strength_standards import (
    get_supported_exercises, normalize_exercise_name,
    get_strength_level, get_standards_table,
)
from fitness_predictor.storage.json_storage import JsonStorage


# ---------------------------------------------------------------------------
# App config & custom CSS
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Fitness & Nutrition Predictor",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for a flashy look
st.markdown("""
<style>
    /* Main gradient header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 { color: white; margin: 0; font-size: 2.2rem; }
    .main-header p { color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0; font-size: 1.1rem; }

    /* Glowing metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }

    /* Styled sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-size: 1.05rem;
        padding: 0.3rem 0;
    }

    /* Card containers */
    .stat-card {
        background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
    }

    /* Chat messages */
    .ai-msg {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-left: 3px solid #667eea;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }

    /* Glowing button */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        transform: translateY(-1px);
    }

    /* Progress bar */
    .stProgress > div > div { border-radius: 10px; }

    /* Form styling */
    .stForm { border-radius: 12px; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { font-weight: 600; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# Persistent storage
storage = JsonStorage()


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.markdown("## 🔥 FitPredict")
st.sidebar.caption("Your AI-Powered Fitness Companion")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Dashboard",
        "👤 Profile",
        "🍽️ Log Nutrition",
        "🏋️ Log Lift",
        "🎯 Macro Targets",
        "📊 1RM Calculator",
        "📋 Reports",
        "🤖 AI Coach",
    ],
)


def get_profile() -> UserProfile | None:
    return storage.load_profile()


def profile_sidebar_summary():
    profile = get_profile()
    if profile:
        st.sidebar.divider()
        total_in = profile.height_cm / 2.54
        ft = int(total_in // 12)
        inches = round(total_in % 12)
        st.sidebar.markdown(f"**👤 {profile.name}**")
        st.sidebar.caption(
            f"💪 {profile.weight_lb:.0f} lbs · 📏 {ft}'{inches}\" · "
            f"🎯 {profile.goal.value.upper()}"
        )


profile_sidebar_summary()

st.sidebar.divider()
st.sidebar.caption("Built with ❤️ + AI")


# ===========================================================================
# PAGES
# ===========================================================================

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
if page == "🏠 Dashboard":
    st.markdown("""
    <div class="main-header">
        <h1>🔥 Fitness & Nutrition Predictor</h1>
        <p>Track your nutrition • Predict your strength • Crush your goals</p>
    </div>
    """, unsafe_allow_html=True)

    profile = get_profile()
    if not profile:
        st.warning("⚠️ No profile set up yet! Head to **👤 Profile** to get started.")
        st.markdown("""
        ### 🚀 Get Started in 3 Steps
        1. **Set up your profile** — Enter your stats (weight, height, age, goals)
        2. **Log your meals & lifts** — Track daily nutrition and gym sessions
        3. **Get predictions** — AI-powered macro targets and 1RM estimates
        """)
        st.stop()

    targets = calculate_macro_targets(profile)

    # Hero metrics
    st.subheader("🎯 Daily Targets")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔥 Calories", f"{targets.calories:.0f}", "kcal")
    col2.metric("🥩 Protein", f"{targets.protein_g:.0f}g")
    col3.metric("🍞 Carbs", f"{targets.carbs_g:.0f}g")
    col4.metric("🥑 Fats", f"{targets.fats_g:.0f}g")

    st.divider()

    # Today's intake vs targets
    col_left, col_right = st.columns(2)

    with col_left:
        today_logs = storage.load_nutrition_logs(start_date=date.today(), end_date=date.today())
        if today_logs:
            total_cal = sum(l.calories for l in today_logs)
            total_p = sum(l.protein_g for l in today_logs)
            total_c = sum(l.carbs_g for l in today_logs)
            total_f = sum(l.fats_g for l in today_logs)

            st.subheader("📊 Today's Progress")
            pct = min(total_cal / targets.calories, 1.0) if targets.calories > 0 else 0
            st.progress(pct, text=f"Calories: {total_cal:.0f} / {targets.calories:.0f} ({pct:.0%})")

            pct_p = min(total_p / targets.protein_g, 1.0) if targets.protein_g > 0 else 0
            st.progress(pct_p, text=f"Protein: {total_p:.0f}g / {targets.protein_g:.0f}g ({pct_p:.0%})")

            pct_c = min(total_c / targets.carbs_g, 1.0) if targets.carbs_g > 0 else 0
            st.progress(pct_c, text=f"Carbs: {total_c:.0f}g / {targets.carbs_g:.0f}g ({pct_c:.0%})")

            pct_f = min(total_f / targets.fats_g, 1.0) if targets.fats_g > 0 else 0
            st.progress(pct_f, text=f"Fats: {total_f:.0f}g / {targets.fats_g:.0f}g ({pct_f:.0%})")
        else:
            st.subheader("📊 Today's Progress")
            st.info("🍽️ No meals logged today — go to **Log Nutrition** to start!")

    with col_right:
        recent_lifts = storage.load_lift_logs()
        if recent_lifts:
            st.subheader("🏋️ Recent Lifts")
            recent = sorted(recent_lifts, key=lambda x: x.date, reverse=True)[:5]
            for log in recent:
                est = f"{log.estimated_1rm:.0f}" if log.estimated_1rm else "?"
                st.markdown(
                    f"**{log.exercise}** — {log.weight} {log.unit.value} × {log.reps} "
                    f"*(1RM ≈ {est} {log.unit.value})* · `{log.date}`"
                )
        else:
            st.subheader("🏋️ Recent Lifts")
            st.info("🏋️ No lifts logged yet — go to **Log Lift** to start!")


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
elif page == "👤 Profile":
    st.markdown("""
    <div class="main-header">
        <h1>👤 Your Profile</h1>
        <p>Set up your biometrics to unlock personalized predictions</p>
    </div>
    """, unsafe_allow_html=True)

    profile = get_profile()
    default_lbs = profile.weight_lb if profile else 154.0
    default_total_inches = profile.height_cm / 2.54 if profile else 67.0
    default_feet = int(default_total_inches // 12)
    default_inches = round(default_total_inches % 12)

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📋 Basic Info")
            name = st.text_input("Name", value=profile.name if profile else "")
            age = st.number_input("Age", min_value=1, max_value=120,
                                  value=profile.age if profile else 25)
            st.caption("📏 Height")
            hcol1, hcol2 = st.columns(2)
            with hcol1:
                height_ft = st.number_input("Feet", min_value=3, max_value=8, value=default_feet)
            with hcol2:
                height_in = st.number_input("Inches", min_value=0, max_value=11, value=default_inches)
            weight_lbs = st.number_input("⚖️ Weight (lbs)", min_value=50.0, max_value=700.0,
                                         value=round(default_lbs, 1), step=1.0)

        with col2:
            st.markdown("#### 🎯 Goals & Activity")
            sex = st.selectbox("Sex", [s.value for s in Sex],
                               index=[s.value for s in Sex].index(profile.sex.value) if profile else 0)
            activity = st.selectbox("Activity Level", [a.value for a in ActivityLevel],
                                    index=[a.value for a in ActivityLevel].index(
                                        profile.activity_level.value) if profile else 2)
            goal = st.selectbox("Goal", [g.value for g in Goal],
                                index=[g.value for g in Goal].index(profile.goal.value) if profile else 2)
            sessions = st.number_input("Training sessions/week", min_value=0, max_value=14,
                                       value=profile.training_sessions_per_week if profile else 3)
            intensity = st.slider("Training intensity", 0.0, 1.0,
                                  value=profile.training_intensity if profile else 0.7)

        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)
        if submitted and name.strip():
            height_cm = (height_ft * 12 + height_in) * 2.54
            weight_kg = weight_lbs * 0.453592
            new_profile = UserProfile(
                name=name.strip(), age=age, height_cm=height_cm, weight_kg=weight_kg,
                sex=Sex(sex), activity_level=ActivityLevel(activity), goal=Goal(goal),
                training_sessions_per_week=sessions, training_intensity=intensity,
            )
            storage.save_profile(new_profile)
            st.success("✅ Profile saved successfully!")
            st.balloons()
            st.rerun()

    if profile:
        st.divider()
        total_in = profile.height_cm / 2.54
        disp_ft = int(total_in // 12)
        disp_in = round(total_in % 12)
        st.markdown(f"""
        ### Current Profile
        | Stat | Value |
        |------|-------|
        | **Name** | {profile.name} |
        | **Age** | {profile.age} years |
        | **Height** | {disp_ft}'{disp_in}" |
        | **Weight** | {profile.weight_lb:.1f} lbs |
        | **Sex** | {profile.sex.value} |
        | **Activity** | {profile.activity_level.value} |
        | **Goal** | {profile.goal.value.upper()} |
        | **Training** | {profile.training_sessions_per_week}×/week @ {profile.training_intensity:.0%} |
        """)


# ---------------------------------------------------------------------------
# Log Nutrition
# ---------------------------------------------------------------------------
elif page == "🍽️ Log Nutrition":
    st.markdown("""
    <div class="main-header">
        <h1>🍽️ Nutrition Logger</h1>
        <p>Track your daily caloric intake and macronutrient breakdown</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Log New Meal", "📜 History"])

    with tab1:
        with st.form("nutrition_form"):
            log_date = st.date_input("📅 Date", value=date.today())
            col1, col2 = st.columns(2)
            with col1:
                calories = st.number_input("🔥 Calories (kcal)", min_value=0.0, value=0.0, step=50.0)
                protein = st.number_input("🥩 Protein (g)", min_value=0.0, value=0.0, step=5.0)
            with col2:
                carbs = st.number_input("🍞 Carbs (g)", min_value=0.0, value=0.0, step=5.0)
                fats = st.number_input("🥑 Fats (g)", min_value=0.0, value=0.0, step=5.0)
            notes = st.text_input("📝 Notes (optional)")

            submitted = st.form_submit_button("💾 Save Meal", use_container_width=True)
            if submitted:
                entry = NutritionLog(
                    date=log_date, calories=calories,
                    protein_g=protein, carbs_g=carbs, fats_g=fats, notes=notes,
                )
                storage.save_nutrition_log(entry)
                st.success(f"✅ Logged: {calories:.0f} kcal | P: {protein:.0f}g | "
                           f"C: {carbs:.0f}g | F: {fats:.0f}g")
                st.balloons()

    with tab2:
        logs = storage.load_nutrition_logs()
        if logs:
            df = pd.DataFrame([{
                "Date": str(l.date), "Calories": f"{l.calories:.0f}",
                "Protein": f"{l.protein_g:.0f}g", "Carbs": f"{l.carbs_g:.0f}g",
                "Fats": f"{l.fats_g:.0f}g", "Notes": l.notes or "—",
            } for l in sorted(logs, key=lambda x: x.date, reverse=True)])
            st.dataframe(df, use_container_width=True, hide_index=True)

            with st.expander("🗑️ Delete an entry"):
                del_date = st.date_input("Select date to delete:", key="del_nutr")
                if st.button("Delete", type="secondary"):
                    if storage.delete_nutrition_log(del_date):
                        st.success(f"Deleted entry for {del_date}")
                        st.rerun()
                    else:
                        st.warning(f"No entry found for {del_date}")
        else:
            st.info("No nutrition entries yet. Log your first meal! 🍕")


# ---------------------------------------------------------------------------
# Log Lift
# ---------------------------------------------------------------------------
elif page == "🏋️ Log Lift":
    st.markdown("""
    <div class="main-header">
        <h1>🏋️ Lift Logger</h1>
        <p>Track your sets and automatically calculate your estimated 1RM</p>
    </div>
    """, unsafe_allow_html=True)

    profile = get_profile()
    tab1, tab2 = st.tabs(["➕ Log New Set", "📜 History"])

    with tab1:
        with st.form("lift_form"):
            log_date = st.date_input("📅 Date", value=date.today())
            exercise = st.text_input("🏋️ Exercise", placeholder="e.g. Bench Press, Squat, Deadlift")
            col1, col2, col3 = st.columns(3)
            with col1:
                weight = st.number_input("⚖️ Weight", min_value=0.1, value=135.0, step=5.0)
            with col2:
                reps = st.number_input("🔁 Reps", min_value=1, max_value=50, value=5)
            with col3:
                unit = st.selectbox("Unit", ["lb", "kg"])

            submitted = st.form_submit_button("💾 Save Lift", use_container_width=True)
            if submitted and exercise.strip():
                w_unit = WeightUnit.LB if unit == "lb" else WeightUnit.KG
                nutrition_logs = storage.load_nutrition_logs()
                result = calculate_1rm(
                    weight=weight, reps=reps, unit=w_unit,
                    exercise=exercise.strip(), profile=profile,
                    nutrition_logs=nutrition_logs or None,
                )
                entry = LiftLog(
                    date=log_date, exercise=exercise.strip(),
                    weight=weight, reps=reps, unit=w_unit,
                    estimated_1rm=result.average_1rm,
                )
                storage.save_lift_log(entry)
                st.success(f"✅ {exercise} — {weight} {unit} × {reps} reps")
                st.metric("⭐ Estimated 1RM", f"{result.average_1rm:.1f} {unit}")
                st.balloons()

    with tab2:
        logs = storage.load_lift_logs()
        if logs:
            df = pd.DataFrame([{
                "Date": str(l.date), "Exercise": l.exercise,
                "Weight": f"{l.weight} {l.unit.value}", "Reps": l.reps,
                "Est. 1RM": f"{l.estimated_1rm:.1f}" if l.estimated_1rm else "—",
            } for l in sorted(logs, key=lambda x: x.date, reverse=True)])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No lifts logged yet. Hit the gym! 💪")


# ---------------------------------------------------------------------------
# Macro Targets
# ---------------------------------------------------------------------------
elif page == "🎯 Macro Targets":
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Calorie & Macro Targets</h1>
        <p>Personalized nutrition targets based on your biometrics and goals</p>
    </div>
    """, unsafe_allow_html=True)

    profile = get_profile()
    if not profile:
        st.warning("⚠️ Set up your profile first!")
        st.stop()

    targets = calculate_macro_targets(profile)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⚡ BMR", f"{targets.bmr:.0f} kcal")
    with col2:
        st.metric("🔥 TDEE", f"{targets.tdee:.0f} kcal")
    with col3:
        st.metric("🎯 Daily Target", f"{targets.calories:.0f} kcal")

    st.divider()
    st.subheader("Macronutrient Breakdown")

    col1, col2, col3 = st.columns(3)
    col1.metric("🥩 Protein", f"{targets.protein_g:.0f}g", f"{targets.protein_g * 4:.0f} kcal")
    col2.metric("🍞 Carbs", f"{targets.carbs_g:.0f}g", f"{targets.carbs_g * 4:.0f} kcal")
    col3.metric("🥑 Fats", f"{targets.fats_g:.0f}g", f"{targets.fats_g * 9:.0f} kcal")

    # Pie chart
    st.divider()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')
    sizes = [targets.protein_g * 4, targets.carbs_g * 4, targets.fats_g * 9]
    labels = [f"Protein\n{targets.protein_g:.0f}g", f"Carbs\n{targets.carbs_g:.0f}g",
              f"Fats\n{targets.fats_g:.0f}g"]
    colors = ["#ff6b6b", "#4ecdc4", "#ffe66d"]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=90, textprops={"fontsize": 12, "color": "white"},
    )
    for autotext in autotexts:
        autotext.set_fontweight("bold")
    ax.set_title("Caloric Distribution", fontsize=16, fontweight="bold", color="white")
    st.pyplot(fig)
    plt.close()


# ---------------------------------------------------------------------------
# 1RM Calculator
# ---------------------------------------------------------------------------
elif page == "📊 1RM Calculator":
    st.markdown("""
    <div class="main-header">
        <h1>📊 One-Rep Max Calculator</h1>
        <p>Estimate your max strength using 5 proven formulas</p>
    </div>
    """, unsafe_allow_html=True)

    profile = get_profile()

    col1, col2 = st.columns([2, 1])
    with col1:
        exercise = st.text_input("🏋️ Exercise", placeholder="e.g. Bench Press")
        weight = st.number_input("⚖️ Weight lifted", min_value=0.1, value=135.0, step=5.0)
    with col2:
        reps = st.number_input("🔁 Reps performed", min_value=1, max_value=50, value=5)
        unit = st.selectbox("Unit", ["lb", "kg"], key="orm_unit")

    if st.button("⚡ Calculate 1RM", use_container_width=True, type="primary") and exercise.strip():
        w_unit = WeightUnit.LB if unit == "lb" else WeightUnit.KG
        nutrition_logs = storage.load_nutrition_logs()
        result = calculate_1rm(
            weight=weight, reps=reps, unit=w_unit,
            exercise=exercise.strip(), profile=profile,
            nutrition_logs=nutrition_logs or None,
        )

        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("⭐ Average 1RM", f"{result.average_1rm:.1f} {unit}")
        if result.adjusted_1rm:
            col2.metric("🔧 Adjusted 1RM", f"{result.adjusted_1rm:.1f} {unit}")
        if result.flagged_formulas:
            col3.warning(f"⚠️ Outliers: {', '.join(result.flagged_formulas)}")

        # Formulas
        st.divider()
        st.subheader("📐 Formula Breakdown")
        formula_cols = st.columns(5)
        formulas = [
            ("Epley", result.epley), ("Brzycki", result.brzycki),
            ("Lombardi", result.lombardi), ("McGlothin", result.mcglothin),
            ("O'Conner", result.oconner),
        ]
        for col, (name, val) in zip(formula_cols, formulas):
            col.metric(name, f"{val:.1f}")

        # Rep percentage table
        st.divider()
        st.subheader("📋 Rep Percentage Table")
        target_reps = st.slider("🎯 Target reps for working weight", 1, 30, 8)
        working = suggested_working_weight(result.average_1rm, target_reps)
        st.success(f"💡 For **{target_reps} reps**, use **{working:.1f} {unit}**")

        rep_data = []
        for r, pct in REP_PERCENTAGES.items():
            rep_weight = result.average_1rm * pct / 100
            highlight = "👉" if r == target_reps else ""
            rep_data.append({"": highlight, "Reps": r, "% 1RM": f"{pct:.0f}%",
                             f"Weight ({unit})": f"{rep_weight:.1f}"})
        st.dataframe(pd.DataFrame(rep_data), use_container_width=True, hide_index=True)

        # Strength standards
        if profile:
            normalized = normalize_exercise_name(exercise)
            if normalized:
                st.divider()
                st.subheader("🏆 Strength Level")
                orm_kg = result.average_1rm * 0.453592 if w_unit == WeightUnit.LB else result.average_1rm
                level = get_strength_level(normalized, orm_kg, profile.weight_kg, profile.sex)
                standards = get_standards_table(normalized, profile.weight_kg, profile.sex)
                conversion = LB_PER_KG if w_unit == WeightUnit.LB else 1.0

                level_icons = {"beginner": "🟤", "novice": "🟢", "intermediate": "🔵",
                               "advanced": "🟣", "elite": "🟡"}
                std_data = []
                for lvl_name, req_kg in standards.items():
                    marker = "◀ YOU" if lvl_name == level.value else ""
                    std_data.append({
                        "": level_icons.get(lvl_name, ""), "Level": lvl_name.upper(),
                        f"Required ({unit})": f"{req_kg * conversion:.1f}", "": marker,
                    })
                st.table(pd.DataFrame(std_data))
                st.success(f"🏆 You are at the **{level.value.upper()}** level!")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
elif page == "📋 Reports":
    st.markdown("""
    <div class="main-header">
        <h1>📋 Reports & Analytics</h1>
        <p>Visualize your progress and track trends over time</p>
    </div>
    """, unsafe_allow_html=True)

    profile = get_profile()
    tab1, tab2 = st.tabs(["📈 Nutrition Trends", "🏋️ Lift Progression"])

    with tab1:
        logs = storage.load_nutrition_logs()
        if logs:
            targets = calculate_macro_targets(profile) if profile else None
            daily: dict[date, dict] = {}
            for log in logs:
                if log.date not in daily:
                    daily[log.date] = {"cal": 0, "p": 0, "c": 0, "f": 0}
                daily[log.date]["cal"] += log.calories
                daily[log.date]["p"] += log.protein_g
                daily[log.date]["c"] += log.carbs_g
                daily[log.date]["f"] += log.fats_g

            df = pd.DataFrame([
                {"Date": d, "Calories": v["cal"], "Protein": v["p"],
                 "Carbs": v["c"], "Fats": v["f"]}
                for d, v in sorted(daily.items())
            ])

            st.subheader("🔥 Calorie Trend")
            chart_data = df.set_index("Date")[["Calories"]]
            if targets:
                chart_data["Target"] = targets.calories
            st.line_chart(chart_data)

            st.subheader("💪 Macro Trends")
            st.line_chart(df.set_index("Date")[["Protein", "Carbs", "Fats"]])

            with st.expander("📊 Raw Data"):
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No nutrition data yet. Start logging meals! 🍽️")

    with tab2:
        lift_logs = storage.load_lift_logs()
        if lift_logs:
            exercises = sorted(set(l.exercise for l in lift_logs))
            selected = st.selectbox("Select exercise", exercises)
            filtered = sorted(
                [l for l in lift_logs if l.exercise == selected],
                key=lambda x: x.date,
            )

            if filtered:
                prog_df = pd.DataFrame([{
                    "Date": l.date, "Weight": l.weight, "Reps": l.reps,
                    "Est. 1RM": l.estimated_1rm or 0,
                } for l in filtered])

                st.subheader(f"📈 {selected} — 1RM Over Time")
                st.line_chart(prog_df.set_index("Date")[["Est. 1RM"]])
                st.dataframe(prog_df, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("🏆 Personal Records")
            pr_data = []
            for ex in exercises:
                ex_logs = [l for l in lift_logs if l.exercise == ex and l.estimated_1rm]
                if ex_logs:
                    best = max(ex_logs, key=lambda l: l.estimated_1rm)
                    pr_data.append({
                        "Exercise": ex, "Best 1RM": f"{best.estimated_1rm:.1f} {best.unit.value}",
                        "Date": str(best.date), "Set": f"{best.weight} × {best.reps}",
                    })
            if pr_data:
                st.table(pd.DataFrame(pr_data))
        else:
            st.info("No lift data yet. Start logging! 🏋️")


# ---------------------------------------------------------------------------
# AI Coach
# ---------------------------------------------------------------------------
elif page == "🤖 AI Coach":
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Fitness Coach</h1>
        <p>Ask me anything about nutrition, training, or your fitness goals</p>
    </div>
    """, unsafe_allow_html=True)

    # Build context from user data
    profile = get_profile()
    context_parts = ["You are a knowledgeable, encouraging fitness and nutrition coach AI. "
                     "Keep answers concise but helpful. Use emojis sparingly."]

    if profile:
        total_in = profile.height_cm / 2.54
        ft = int(total_in // 12)
        inches = round(total_in % 12)
        targets = calculate_macro_targets(profile)
        context_parts.append(
            f"\nUser profile: {profile.name}, {profile.age}yo, {ft}'{inches}\", "
            f"{profile.weight_lb:.0f} lbs, {profile.sex.value}, "
            f"activity={profile.activity_level.value}, goal={profile.goal.value}, "
            f"trains {profile.training_sessions_per_week}x/week."
            f"\nDaily targets: {targets.calories:.0f} cal, {targets.protein_g:.0f}g protein, "
            f"{targets.carbs_g:.0f}g carbs, {targets.fats_g:.0f}g fats. "
            f"BMR={targets.bmr:.0f}, TDEE={targets.tdee:.0f}."
        )

    recent_logs = storage.load_nutrition_logs()
    if recent_logs:
        last_3 = recent_logs[-3:]
        log_str = "; ".join(
            f"{l.date}: {l.calories:.0f}cal, P{l.protein_g:.0f}g, C{l.carbs_g:.0f}g, F{l.fats_g:.0f}g"
            for l in last_3
        )
        context_parts.append(f"\nRecent nutrition: {log_str}")

    lift_logs = storage.load_lift_logs()
    if lift_logs:
        last_3_lifts = lift_logs[-3:]
        lift_str = "; ".join(
            f"{l.exercise}: {l.weight}{l.unit.value}x{l.reps} (1RM≈{l.estimated_1rm:.0f})"
            for l in last_3_lifts if l.estimated_1rm
        )
        if lift_str:
            context_parts.append(f"\nRecent lifts: {lift_str}")

    system_prompt = "\n".join(context_parts)

    # Check for API key
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        st.info("""
        ### 🔑 Set Up AI Coach

        To enable the AI Coach, you need a free Gemini API key:

        1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
        2. Click **Create API Key**
        3. Paste it below:
        """)
        user_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...")
        if user_key:
            os.environ["GEMINI_API_KEY"] = user_key
            api_key = user_key
            st.success("✅ API key set! Start chatting below.")
            st.rerun()
        else:
            st.stop()

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🏋️" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # Suggested prompts
    if not st.session_state.messages:
        st.markdown("#### 💡 Try asking:")
        suggestions = st.columns(3)
        prompts = [
            "What should I eat before a heavy deadlift session?",
            "How can I break through a bench press plateau?",
            "Am I eating enough protein for my goals?",
        ]
        for col, prompt in zip(suggestions, prompts):
            if col.button(prompt, use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()

    # Chat input
    if user_input := st.chat_input("Ask your AI coach anything..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🏋️"):
            st.markdown(user_input)

        # Call Gemini
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)

                    # Build conversation history
                    contents = [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + st.session_state.messages[0]["content"]}]}]
                    if len(st.session_state.messages) > 1:
                        contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
                        for msg in st.session_state.messages:
                            role = "user" if msg["role"] == "user" else "model"
                            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents,
                    )
                    reply = response.text
                except Exception as e:
                    reply = f"⚠️ Error connecting to AI: {str(e)}\n\nMake sure your API key is valid."

                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
