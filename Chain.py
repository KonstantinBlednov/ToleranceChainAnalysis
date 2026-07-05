import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import math

# Настройка страницы
st.set_page_config(
    page_title="Расчет размерных цепей",
    page_icon="📐",
    layout="wide"
)

# Стилизация интерфейса с помощью CSS для адаптивной верстки (Light/Dark themes)
st.markdown("""
<style>
    .reportview-container {
        background: #f5f7f9;
    }
    .main-header {
        font-size: 2.2rem;
        color: var(--primary-color, #1E3A8A);
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: var(--text-color, #4B5563) !important;
        opacity: 0.95;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    /* Карточка результатов адаптируется под темную/светлую тему */
    .result-card {
        background-color: var(--secondary-background-color, #F3F4F6);
        color: var(--text-color, #1F2937);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .result-card h4 {
        color: var(--text-color, #1E3A8A) !important;
        margin-top: 0px;
    }
    .result-card li {
        color: var(--text-color, #1F2937);
    }
    /* Стилизация inline-кода в результатах под текущую тему */
    .result-card code {
        background-color: var(--background-color, #FFFFFF) !important;
        color: var(--text-color, #111827) !important;
        font-size: 0.95rem;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-weight: bold;
    }
    /* Специфические цвета для ключевых характеристик, видимые на любом фоне */
    .result-card .metric-nominal {
        font-size: 1.1rem !important;
        font-weight: bold;
        color: var(--primary-color, #1E3A8A) !important;
    }
    .result-card .metric-es {
        color: #10B981 !important; /* Яркий зеленый */
        font-weight: bold;
    }
    .result-card .metric-ei {
        color: #EF4444 !important; /* Яркий красный */
        font-weight: bold;
    }
    /* Карточка ошибки фиксируется в читаемых темных тонах на светлом фоне */
    .error-card {
        background-color: #FEF2F2;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #EF4444;
        margin-bottom: 1rem;
    }
    .error-card, .error-card * {
        color: #991B1B !important;
    }
    /* Стили для принудительного переноса слов в заголовках таблиц Streamlit */
    div[data-testid="stTable"] th, 
    div[data-testid="stDataFrameData"] th {
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* === НАСТРОЙКА КОНТРАСТНЫХ ВСПЛЫВАЮЩИХ ПОДСКАЗОК (TOOLTIPS) === */
    /* Делаем фон строго белым, шрифт темным и добавляем черную рамку для контраста в любой теме */
    div[data-testid="stTooltipContent"], 
    div[role="tooltip"],
    .stTooltipContent {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        border-radius: 6px !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.3) !important;
        padding: 12px !important;
    }
    /* Гарантируем, что весь текст внутри подсказки принудительно окрасится в черный цвет */
    div[data-testid="stTooltipContent"] *, 
    div[role="tooltip"] *,
    .stTooltipContent * {
        color: #000000 !important;
        background-color: transparent !important;
        font-family: inherit !important;
        font-size: 0.9rem !important;
        line-height: 1.4 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📐 Интерактивный расчет размерных цепей</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Проектирование и верификация линейных размерных цепей с использованием Worst-Case, классического RSS и статистического анализа Six Sigma.</div>', unsafe_allow_html=True)

# Вспомогательная функция Лапласа (CDF стандартного нормального распределения) через math.erf
def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

# Боковая панель настроек
with st.sidebar:
    st.header("⚙️ Параметры расчета")
    
    task_type = st.radio(
        "Тип решаемой задачи:",
        ["Обратная задача (Расчет замыкающего звена)", "Прямая задача (Расчет звеньев цепи)"],
        help="Обратная задача: находим параметры замыкающего звена по известным составляющим. Прямая задача: находим допуски составляющих звеньев по заданным параметрам замыкающего звена."
    )
    
    # Поля ввода для Прямой задачи (параметры замыкающего звена A_delta)
    if "Прямая задача" in task_type:
        st.subheader("🎯 Параметры замыкающего звена A_Δ")
        a_delta_nom = st.number_input("Номинал A_Δ, мм", value=5.000, step=0.100, format="%.3f")
        a_delta_es = st.number_input("Верхнее откл. ES_Δ, мм", value=0.100, step=0.010, format="%.3f")
        a_delta_ei = st.number_input("Нижнее откл. EI_Δ, мм", value=-0.100, step=0.010, format="%.3f")
        
        if a_delta_ei > a_delta_es:
            st.error("Ошибка: Нижнее отклонение должно быть меньше верхнего!")
            a_delta_ei = a_delta_es - 0.01
    else:
        a_delta_nom, a_delta_es, a_delta_ei = 5.0, 0.1, -0.1 # Дефолтные значения (не отображаются)

    method = st.selectbox(
        "Метод расчета:",
        ["Максимум-Минимум (Worst-Case)", "Классический RSS (Квадратичный)", "Статистический анализ (Six Sigma)"],
        help=(
            "1.  Максимум-Минимум: Гарантирует 100% собираемость при наихудшем сочетании размеров.\n"
            "2.  Классический RSS: Простой квадратичный допуск T_Δ = sqrt(sum(T_i^2)).\n"
            "3.  Статистический анализ (Six Sigma): Полноценный расчет среднеквадратичного отклонения сборки, PPM брака и уровня качества."
        )
    )
    
    # Специфические настройки для вероятностного / Six Sigma режима
    if method == "Статистический анализ (Six Sigma)":
        st.subheader("📊 Параметры надежности")
        
        # Целевой уровень качества показывается ТОЛЬКО для прямой задачи (когда мы синтезируем допуски)
        if "Прямая задача" in task_type:
            quality_level = st.selectbox(
                "Целевой уровень качества (Конструкторская часть):",
                ["3 Сигма (0.27% брака)", "2.57 Сигма (1.00% брака)", "4 Сигма (0.0063% брака)", "10 PPM / 0.001% (4.417 Сигма)"],
                index=0, # По умолчанию 3 Сигма
                help=(
                    "КОНСТРУКТОРСКАЯ ЧАСТЬ. Задает жесткость требований к сборке.\n\n"
                    "Определяет допустимую вероятность выхода параметров замыкающего звена за установленные конструктором пределы. "
                    "Влияет на расчет допусков деталей в таблице: чем более высокий уровень надежности требуется (меньше брака), "
                    "тем сильнее программа сожмет (уменьшит) допуски составляющих деталей."
                )
            )
            
            # Коэффициенты t соответствующие выбранным уровням брака
            t_map = {
                "3 Сигма (0.27% брака)": 3.0,
                "2.57 Сигма (1.00% брака)": 2.57,
                "4 Сигма (0.0063% брака)": 4.0,
                "10 PPM / 0.001% (4.417 Сигма)": 4.417
            }
            t_coeff = t_map[quality_level]
        else:
            t_coeff = 3.0
            quality_level = "N/A (Расчет фактического брака)"
        
        cp_detail = st.number_input(
            "Воспроизводимость деталей Cp (Технологическая часть):",
            min_value=0.50,
            max_value=2.50,
            value=1.00,
            step=0.05,
            help=(
                "ТЕХНОЛОГИЧЕСКАЯ ЧАСТЬ. Отражает реальную точность и стабильность оборудования на заводе.\n\n"
                "Этот коэффициент берется по факту измерений уже изготовленных партий деталей. "
                "Он равен отношению ширины конструкторского допуска детали к ее технологическому разбросу (Cp = T / 6σ):\n\n"
                "* **Cp = 1.00** — стандартное стабильное производство (ширина допуска точно равна разбросу 6σ).\n"
                "* **Cp < 1.00** — нестабильный процесс (высокий разброс, оборудование не держит точность, много брака деталей).\n"
                "* **Cp > 1.00** — прецизионный стабильный процесс (технологический разброс значительно меньше допуска)."
            )
        )
    else:
        t_coeff = 3.0
        cp_detail = 1.0
        quality_level = "N/A"

    st.markdown("---")
    st.markdown("""
    **Справка по терминам:**
    * **Увеличивающее звено ($A_i \\uparrow$):** Звено, с увеличением которого замыкающее звено увеличивается.
    * **Уменьшающее звено ($A_i \\downarrow$):** Звено, с увеличением которого замыкающее звено уменьшается.
    * **Замыкающее звено ($A_\\Delta$):** Финальный зазор или размер, получаемый в результате сборки.
    """)

# Инициализация начальных данных в состоянии сессии при смене режима задач
if "chain_data" not in st.session_state or "last_task_type" not in st.session_state or st.session_state.last_task_type != task_type:
    st.session_state.last_task_type = task_type
    
    # Базовый набор данных
    init_data = [
        {"Название": "A1", "Номинал, мм": 50.0, "Верхнее откл., мм": 0.15, "Нижнее откл., мм": -0.05, "Тип": "Увеличивающее (+)", "Вручную": False, "Компенсатор": False, "Поле допуска": "Симметрично (±)"},
        {"Название": "A2", "Номинал, мм": 30.0, "Верхнее откл., мм": 0.10, "Нижнее откл., мм": -0.10, "Тип": "Уменьшающее (-)", "Вручную": False, "Компенсатор": False, "Поле допуска": "Вал (h)"},
        {"Название": "A3", "Номинал, мм": 15.0, "Верхнее откл., мм": 0.05, "Нижнее откл., мм": -0.05, "Тип": "Уменьшающее (-)", "Вручную": False, "Компенсатор": True, "Поле допуска": "Симметрично (±)"},
    ]
    
    init_df = pd.DataFrame(init_data)
    init_df["Допуск, мм"] = init_df["Верхнее откл., мм"] - init_df["Нижнее откл., мм"]
    init_df["Середина поля допуска, мм"] = (init_df["Верхнее откл., мм"] + init_df["Нижнее откл., мм"]) / 2
    init_df["Номинал в середине поля, мм"] = init_df["Номинал, мм"] + init_df["Середина поля допуска, мм"]
    st.session_state.chain_data = init_df

# Основной контент (последовательный вывод сверху вниз)
st.subheader("📋 Составляющие звенья цепи")
st.write("Вы можете редактировать таблицу: менять размеры, добавлять новые строки снизу (кнопка **Add row**) или удалять ненужные. Имена звеньев генерируются автоматически при создании, но вы можете изменить их вручную.")

# Конфигурация колонок в зависимости от типа задачи
if "Прямая задача" in task_type:
    col_config = {
        "Название": st.column_config.TextColumn("Название", help="Название или номер звена (например, А1, Б1). Вы можете изменить его вручную.", width=120, required=True),
        "Номинал, мм": st.column_config.NumberColumn("Номинал, мм", help="Номинальный размер звена. Для компенсатора номинал рассчитывается автоматически.", min_value=0.000, format="%.3f", width=100, required=True),
        "Вручную": st.column_config.CheckboxColumn("Вручную", help="Заморозить допуск и ввести отклонения вручную.", width=70, default=False),
        "Верхнее откл., мм": st.column_config.NumberColumn("ES", help="Верхнее предельное отклонение со знаком (вручную).", format="%.3f", width=60),
        "Нижнее откл., мм": st.column_config.NumberColumn("EI", help="Нижнее предельное отклонение со знаком (вручную).", format="%.3f", width=60),
        "Допуск, мм": st.column_config.NumberColumn("T", help="Допуск размера (Т = ES - EI) [Рассчитывается автоматически]", format="%.3f", width=60, disabled=True),
        "Середина поля допуска, мм": st.column_config.NumberColumn("Ec", help="Середина поля допуска (ES + EI)/2 [Рассчитывается автоматически]", format="%.3f", width=60, disabled=True),
        "Номинал в середине поля, мм": st.column_config.NumberColumn("Ac", help="Номинал в середине поля (Номинал + Ec) [Рассчитывается автоматически]", format="%.3f", width=60, disabled=True),
        "Тип": st.column_config.SelectboxColumn("Тип звена", help="Увеличивающее или уменьшающее звено", options=["Увеличивающее (+)", "Уменьшающее (-)"], width=130, required=True),
        "Компенсатор": st.column_config.CheckboxColumn("Компенсатор", help="Назначить компенсатором. Номинал и допуск этого звена будут рассчитаны автоматически.", width=90, default=False),
        "Поле допуска": st.column_config.SelectboxColumn("Поле допуска", help="Схема расположения допуска для авто-расчета", options=["Симметрично (±)", "Отверстие (H)", "Вал (h)"], width=130, required=True)
    }
    columns_to_disable = ["Допуск, мм", "Середина поля допуска, мм", "Номинал в середине поля, мм"]
    
    # Измененный порядок колонок по вашему запросу: название - номинал - вручную - компенсатор - тип звена - поле допуска ... и далее по порядку
    column_order = ["Название", "Номинал, мм", "Вручную", "Компенсатор", "Тип", "Поле допуска", "Верхнее откл., мм", "Нижнее откл., мм", "Допуск, мм", "Середина поля допуска, мм", "Номинал в середине поля, мм"]
else:
    col_config = {
        "Название": st.column_config.TextColumn("Название", help="Название или номер звена (например, А1, Б1). Вы можете изменить его вручную.", width=120, required=True),
        "Номинал, мм": st.column_config.NumberColumn("Номинал, мм", help="Номинальный размер составляющего звена в миллиметрах", min_value=0.001, format="%.3f", width=100, required=True),
        "Верхнее откл., мм": st.column_config.NumberColumn("ES", help="Верхнее предельное отклонение размера со знаком (ES), мм", format="%.3f", width=60, required=True),
        "Нижнее откл., мм": st.column_config.NumberColumn("EI", help="Нижнее предельное отклонение размера со знаком (EI), мм", format="%.3f", width=60, required=True),
        "Допуск, мм": st.column_config.NumberColumn("T", help="Допуск размера (T = ES - EI), мм [Вычисляется автоматически]", format="%.3f", width=60, disabled=True),
        "Середина поля допуска, мм": st.column_config.NumberColumn("Ec", help="Координата середины поля допуска Ec = (ES + EI) / 2, мм [Вычисляется автоматически]", format="%.3f", width=60, disabled=True),
        "Номинал в середине поля, мм": st.column_config.NumberColumn("Ac", help="Размер по середине поля допуска Ac = Номинал + Ec, мм [Вычисляется автоматически]", format="%.3f", width=60, disabled=True),
        "Тип": st.column_config.SelectboxColumn("Тип звена", help="Тип звена: увеличивающее (+) или уменьшающее (-)", options=["Увеличивающее (+)", "Уменьшающее (-)"], width=130, required=True)
    }
    columns_to_disable = ["Допуск, мм", "Середина поля допуска, мм", "Номинал в середине поля, мм"]
    column_order = ["Название", "Номинал, мм", "Верхнее откл., мм", "Нижнее откл., мм", "Допуск, мм", "Середина поля допуска, мм", "Номинал в середине поля, мм", "Тип"]

# Отрисовка интерактивного редактора данных
edited_df = st.data_editor(
    st.session_state.chain_data,
    num_rows="dynamic",
    column_config=col_config,
    disabled=columns_to_disable,
    column_order=column_order,
    key="editor",
    use_container_width=True
)

# Подготовка копии для безопасного пересчета
updated_df = edited_df.copy()

# Заполнение временных NaN значений при создании новых строк
for col in ["Номинал, мм", "Верхнее откл., мм", "Нижнее откл., мм"]:
    if col in updated_df.columns:
        updated_df[col] = pd.to_numeric(updated_df[col]).fillna(0.0)
if "Вручную" in updated_df.columns:
    updated_df["Вручную"] = updated_df["Вручную"].fillna(False)
if "Компенсатор" in updated_df.columns:
    updated_df["Компенсатор"] = updated_df["Компенсатор"].fillna(False)
if "Поле допуска" in updated_df.columns:
    updated_df["Поле допуска"] = updated_df["Поле допуска"].fillna("Симметрично (±)")
updated_df["Тип"] = updated_df["Тип"].fillna("Увеличивающее (+)")

# Автоматическая генерация имен/номеров звеньев (A1, A2, A3...) по порядку
for i in range(len(updated_df)):
    current_name = updated_df.iloc[i]["Название"]
    if pd.isna(current_name) or str(current_name).strip() == "" or str(current_name) == "None":
        updated_df.at[updated_df.index[i], "Название"] = f"A{i+1}"

# ==================== ИНТЕРАКТИВНЫЙ БЛОК ЗАЩИТЫ (ВАЛИДАЦИЯ ГАЛОЧЕК) ====================
if "Прямая задача" in task_type and not updated_df.empty and "chain_data" in st.session_state:
    old_df = st.session_state.chain_data
    
    # 1. Защита от выбора нескольких компенсаторов (интерактивное радио-поведение)
    new_comp_indices = updated_df[updated_df["Компенсатор"] == True].index.tolist()
    if len(new_comp_indices) > 1:
        newly_checked = None
        for idx in new_comp_indices:
            # Ищем индекс, который в старых данных компенсатором НЕ был (значит, по нему кликнули только что)
            if idx in old_df.index and not old_df.at[idx, "Компенсатор"]:
                newly_checked = idx
                break
        
        if newly_checked is not None:
            for idx in new_comp_indices:
                if idx != newly_checked:
                    updated_df.at[idx, "Компенсатор"] = False
        else:
            # Если не удалось определить (например, при добавлении строк), оставляем первый
            for idx in new_comp_indices[1:]:
                updated_df.at[idx, "Компенсатор"] = False
                
    # 2. Защита от взаимного пересечения "Вручную" и "Компенсатор" на одной строке
    for idx in updated_df.index:
        if updated_df.at[idx, "Вручную"] and updated_df.at[idx, "Компенсатор"]:
            if idx in old_df.index:
                was_manual = old_df.at[idx, "Вручную"]
                was_comp = old_df.at[idx, "Компенсатор"]
                
                if was_comp and not was_manual:
                    # Пользователь включил "Вручную" на компенсаторе -> снимаем флаг компенсатора
                    updated_df.at[idx, "Компенсатор"] = False
                elif was_manual and not was_comp:
                    # Пользователь назначил компенсатором ручную деталь -> отменяем ручной режим допуска
                    updated_df.at[idx, "Вручную"] = False
                else:
                    updated_df.at[idx, "Вручную"] = False
            else:
                updated_df.at[idx, "Вручную"] = False

# ==================== АЛГОРИТМ ПРЯМОЙ ЗАДАЧИ (СИНТЕЗ ЦЕПИ) ====================
if "Прямая задача" in task_type and not updated_df.empty:
    # Определение компенсирующего звена (проверка отсутствия)
    comp_mask = updated_df["Компенсатор"] == True
    num_compensators = comp_mask.sum()
    
    if num_compensators == 0:
        # Если ни один компенсатор не выбран, ищем последнее звено, у которого НЕ стоит "Вручную"
        non_manual_indices = updated_df[updated_df["Вручную"] == False].index.tolist()
        if non_manual_indices:
            comp_idx = non_manual_indices[-1]
        else:
            # Если вообще все звенья ручные, берем последнее и принудительно снимаем с него блокировку
            comp_idx = updated_df.index[-1]
            updated_df.at[comp_idx, "Вручную"] = False
        updated_df.at[comp_idx, "Компенсатор"] = True
                    
    comp_idx = updated_df[updated_df["Компенсатор"] == True].index[0]
    updated_df.at[comp_idx, "Вручную"] = False
    
    # 2. Расчет номинального размера компенсатора
    other_inc = updated_df[(updated_df.index != comp_idx) & (updated_df["Тип"] == "Увеличивающее (+)")]
    other_dec = updated_df[(updated_df.index != comp_idx) & (updated_df["Тип"] == "Уменьшающее (-)")]
    
    sum_other_inc = other_inc["Номинал, мм"].sum()
    sum_other_dec = other_dec["Номинал, мм"].sum()
    
    comp_type = updated_df.at[comp_idx, "Тип"]
    if comp_type == "Увеличивающее (+)":
        comp_nominal = a_delta_nom - sum_other_inc + sum_other_dec
    else:
        comp_nominal = sum_other_inc - sum_other_dec - a_delta_nom
        
    updated_df.at[comp_idx, "Номинал, мм"] = comp_nominal
    
    # 3. Расчет допусков методом равной точности (квалитетов)
    # Единица допуска: i = 0.45 * D^(1/3) + 0.001 * D
    def calc_unit_tolerance(d):
        if d <= 0:
            return 0.001
        return 0.45 * (d ** (1/3)) + 0.001 * d

    updated_df["i_unit"] = updated_df["Номинал, мм"].apply(calc_unit_tolerance)
    t_delta = a_delta_es - a_delta_ei # Конструкторский допуск замыкающего звена
    
    # Расчет допусков для замороженных вручную звеньев
    manual_mask = (updated_df["Вручную"] == True) & (updated_df.index != comp_idx)
    updated_df.loc[manual_mask, "Допуск, мм"] = updated_df.loc[manual_mask, "Верхнее откл., мм"] - updated_df.loc[manual_mask, "Нижнее откл., мм"]
    sum_manual_tol = updated_df.loc[manual_mask, "Допуск, мм"].sum()
    
    # Звенья для автоматического распределения допуска (все незамороженные, исключая компенсатор)
    auto_mask = (updated_df["Вручную"] == False) & (updated_df.index != comp_idx)
    
    # Распределение оставшегося допуска
    if method == "Максимум-Минимум (Worst-Case)":
        all_calc_mask = (updated_df["Вручную"] == False)
        sum_i_all_calc = updated_df.loc[all_calc_mask, "i_unit"].sum()
        rem_tolerance_for_distribution = t_delta - sum_manual_tol
        
        if sum_i_all_calc > 0 and rem_tolerance_for_distribution > 0:
            a_coeff = (rem_tolerance_for_distribution / sum_i_all_calc) * 1000.0  # переводим в мкм
            updated_df.loc[auto_mask, "Допуск, мм"] = (a_coeff * updated_df.loc[auto_mask, "i_unit"]) / 1000.0
        else:
            updated_df.loc[auto_mask, "Допуск, мм"] = 0.0
            
        sum_others_tol = updated_df[updated_df.index != comp_idx]["Допуск, мм"].sum()
        comp_tolerance = t_delta - sum_others_tol
        updated_df.at[comp_idx, "Допуск, мм"] = max(0.0, comp_tolerance)
        
    elif method == "Классический RSS (Квадратичный)":
        sum_manual_tol_sq = (updated_df.loc[manual_mask, "Допуск, мм"] ** 2).sum()
        all_calc_mask = (updated_df["Вручную"] == False)
        sum_i_sq_all_calc = (updated_df.loc[all_calc_mask, "i_unit"] ** 2).sum()
        target_val = t_delta**2 - sum_manual_tol_sq
        
        if sum_i_sq_all_calc > 0 and target_val > 0:
            a_coeff_sq = (target_val / sum_i_sq_all_calc) * 1000000.0  # в мкм
            a_coeff = np.sqrt(a_coeff_sq)
            updated_df.loc[auto_mask, "Допуск, мм"] = (a_coeff * updated_df.loc[auto_mask, "i_unit"]) / 1000.0
        else:
            updated_df.loc[auto_mask, "Допуск, мм"] = 0.0
            
        sum_others_tol_sq = (updated_df[updated_df.index != comp_idx]["Допуск, мм"] ** 2).sum()
        comp_tol_sq = t_delta**2 - sum_others_tol_sq
        updated_df.at[comp_idx, "Допуск, мм"] = np.sqrt(max(0.0, comp_tol_sq))
        
    else:  # Статистический анализ (Six Sigma)
        sigma_target = t_delta / (2.0 * t_coeff)
        var_target = sigma_target ** 2
        
        factor = 6.0 * cp_detail
        updated_df.loc[manual_mask, "sigma"] = updated_df.loc[manual_mask, "Допуск, мм"] / factor
        sum_manual_var = (updated_df.loc[manual_mask, "sigma"] ** 2).sum()
        
        all_calc_mask = (updated_df["Вручную"] == False)
        sum_i_sq_all_calc = (updated_df.loc[all_calc_mask, "i_unit"] ** 2).sum()
        target_var_rem = var_target - sum_manual_var
        
        if sum_i_sq_all_calc > 0 and target_var_rem > 0:
            a_coeff_var = (target_var_rem / sum_i_sq_all_calc)
            updated_df.loc[auto_mask, "sigma"] = np.sqrt(a_coeff_var) * updated_df.loc[auto_mask, "i_unit"]
            updated_df.loc[auto_mask, "Допуск, мм"] = updated_df.loc[auto_mask, "sigma"] * factor
        else:
            updated_df.loc[auto_mask, "Допуск, мм"] = 0.0
            updated_df.loc[auto_mask, "sigma"] = 0.0
            
        sum_others_var = (updated_df[updated_df.index != comp_idx]["Допуск, мм"] / factor) ** 2
        comp_var = var_target - sum_others_var.sum()
        comp_sigma = np.sqrt(max(0.0, comp_var))
        updated_df.at[comp_idx, "Допуск, мм"] = comp_sigma * factor

    # 4. Расчет отклонений ES и EI для авто-звеньев на основе выбранного "Поля допуска"
    for idx in updated_df[auto_mask].index:
        tol = updated_df.at[idx, "Допуск, мм"]
        field_type = updated_df.at[idx, "Поле допуска"]
        
        if field_type == "Симметрично (±)":
            updated_df.at[idx, "Верхнее откл., мм"] = tol / 2.0
            updated_df.at[idx, "Нижнее откл., мм"] = -tol / 2.0
        elif field_type == "Отверстие (H)":
            updated_df.at[idx, "Верхнее откл., мм"] = tol
            updated_df.at[idx, "Нижнее откл., мм"] = 0.0
        elif field_type == "Вал (h)":
            updated_df.at[idx, "Верхнее откл., мм"] = 0.0
            updated_df.at[idx, "Нижнее откл., мм"] = -tol

    # Рассчитаем середины полей допуска для всех звеньев (кроме компенсатора)
    updated_df["Середина поля допуска, мм"] = (updated_df["Верхнее откл., мм"] + updated_df["Нижнее откл., мм"]) / 2
    updated_df["Номинал в середине поля, мм"] = updated_df["Номинал, мм"] + updated_df["Середина поля допуска, мм"]

    # 5. Расчет точных отклонений для Компенсатора, чтобы замкнуть цепь
    others_inc = updated_df[(updated_df.index != comp_idx) & (updated_df["Тип"] == "Увеличивающее (+)")]
    others_dec = updated_df[(updated_df.index != comp_idx) & (updated_df["Тип"] == "Уменьшающее (-)")]
    
    mid_delta = (a_delta_es + a_delta_ei) / 2.0
    sum_other_mid_inc = others_inc["Середина поля допуска, мм"].sum()
    sum_other_mid_dec = others_dec["Середина поля допуска, мм"].sum()
    
    if comp_type == "Увеличивающее (+)":
        comp_mid = mid_delta - sum_other_mid_inc + sum_other_mid_dec
    else:
        comp_mid = sum_other_mid_inc - sum_other_mid_dec - mid_delta
        
    comp_tol = updated_df.at[comp_idx, "Допуск, мм"]
    
    updated_df.at[comp_idx, "Верхнее откл., мм"] = comp_mid + comp_tol / 2.0
    updated_df.at[comp_idx, "Нижнее откл., мм"] = comp_mid - comp_tol / 2.0
    updated_df.at[comp_idx, "Середина поля допуска, мм"] = comp_mid
    updated_df.at[comp_idx, "Номинал в середине поля, мм"] = updated_df.at[comp_idx, "Номинал, мм"] + comp_mid

# ==================== АЛГОРИТМ ОБРАТНОЙ ЗАДАЧИ (РАСЧЕТ ЗАМЫКАЮЩЕГО) ====================
elif "Обратная задача" in task_type and not updated_df.empty:
    updated_df["Допуск, мм"] = updated_df["Верхнее откл., мм"] - updated_df["Нижнее откл., мм"]
    updated_df["Середина поля допуска, мм"] = (updated_df["Верхнее откл., мм"] + updated_df["Нижнее откл., мм"]) / 2
    updated_df["Номинал в середине поля, мм"] = updated_df["Номинал, мм"] + updated_df["Середина поля допуска, мм"]

# Если данные изменились, плавно перезапускаем интерфейс
if not updated_df.equals(st.session_state.chain_data):
    st.session_state.chain_data = updated_df
    st.rerun()

# Работаем с актуальным состоянием данных
edited_df = st.session_state.chain_data

st.markdown("---")

# Раздел расчетов и результатов
if edited_df.empty:
    st.markdown('<div class="error-card">⚠️ Добавьте хотя бы одно звено в таблицу выше для начала расчета.</div>', unsafe_allow_html=True)
else:
    # Валидация введенных отклонений
    invalid_rows = edited_df[edited_df["Нижнее откл., мм"] > edited_df["Верхнее откл., мм"]]
    if not invalid_rows.empty:
        st.markdown(f'<div class="error-card">⚠️ Ошибка: В строках {", ".join(invalid_rows["Название"].astype(str))} нижнее отклонение больше верхнего!</div>', unsafe_allow_html=True)
    else:
        # Расчет итоговых параметров в зависимости от задачи и выбранного математического ядра
        if "Прямая задача" in task_type:
            nominal_delta = a_delta_nom
            es_delta = a_delta_es
            ei_delta = a_delta_ei
            tolerance_delta = es_delta - ei_delta
            max_delta = nominal_delta + es_delta
            min_delta = nominal_delta + ei_delta
            
            # Проверка компенсатора
            comp_row = edited_df[edited_df["Компенсатор"] == True].iloc[0]
            if comp_row["Номинал, мм"] <= 0:
                st.markdown(f'<div class="error-card">⚠️ Предупреждение: Рассчитанный номинал компенсирующего звена {comp_row["Название"]} равен {comp_row["Номинал, мм"]:.3f} мм (отрицательный или нулевой). Проверьте соотношение номинальных размеров составляющих звеньев.</div>', unsafe_allow_html=True)
        else:
            inc_links = edited_df[edited_df["Тип"] == "Увеличивающее (+)"]
            dec_links = edited_df[edited_df["Тип"] == "Уменьшающее (-)"]
            
            sum_inc_nom = inc_links["Номинал, мм"].sum()
            sum_dec_nom = dec_links["Номинал, мм"].sum()
            nominal_delta = sum_inc_nom - sum_dec_nom
            
            if method == "Максимум-Минимум (Worst-Case)":
                es_delta = inc_links["Верхнее откл., мм"].sum() - dec_links["Нижнее откл., мм"].sum()
                ei_delta = inc_links["Нижнее откл., мм"].sum() - dec_links["Верхнее откл., мм"].sum()
                tolerance_delta = edited_df["Допуск, мм"].sum()
            else:
                sum_inc_mid = inc_links["Середина поля допуска, мм"].sum() if not inc_links.empty else 0
                sum_dec_mid = dec_links["Середина поля допуска, мм"].sum() if not dec_links.empty else 0
                mid_delta = sum_inc_mid - sum_dec_mid
                
                squared_sum = (edited_df["Допуск, мм"] ** 2).sum()
                tolerance_delta = np.sqrt(squared_sum)
                
                es_delta = mid_delta + (tolerance_delta / 2)
                ei_delta = mid_delta - (tolerance_delta / 2)

            max_delta = nominal_delta + es_delta
            min_delta = nominal_delta + ei_delta

        # Вывод результатов ниже таблицы
        st.subheader("🎯 Результаты расчета замыкающего звена ($A_\\Delta$)")
        
        col_res_details, col_res_metrics = st.columns([1.2, 0.8])
        
        # Расчет параметров для модуля Six Sigma
        if method == "Статистический анализ (Six Sigma)":
            sigmas = edited_df["Допуск, мм"] / (6.0 * cp_detail)
            sigma_delta = np.sqrt((sigmas ** 2).sum())
            
            design_tolerance = max_delta - min_delta
            cp_assembly = design_tolerance / (6.0 * sigma_delta) if sigma_delta > 0 else 0
            z_score = (design_tolerance / 2.0) / sigma_delta if sigma_delta > 0 else 0
            
            if z_score > 0:
                p_out = 2.0 * (1.0 - normal_cdf(z_score))
                ppm = p_out * 1000000.0
                yield_percent = (1.0 - p_out) * 100.0
            else:
                ppm = 1000000.0
                yield_percent = 0.0
        else:
            sigma_delta = 0
            cp_assembly = 0
            z_score = 0
            ppm = 0
            yield_percent = 0

        with col_res_details:
            st.latex(rf"A_\Delta = {nominal_delta:.3f}^{{+{es_delta:.3f}}}_{{{ei_delta:.3f}}} \text{{ мм}}")
            
            st.markdown(rf"""
            <div class="result-card">
                <h4><b>Расчетные характеристики:</b></h4>
                <ul style="line-height:1.6;">
                    <li><b>Режим расчета:</b> {task_type}</li>
                    <li><b>Метод расчета:</b> {method}</li>
                    <li><b>Номинальный размер ($A_\Delta$):</b> <code class="metric-nominal">{nominal_delta:.3f} мм</code></li>
                    <li><b>Верхнее отклонение ($ES_\Delta$):</b> <code class="metric-es">+{es_delta:.3f} мм</code></li>
                    <li><b>Нижнее отклонение ($EI_\Delta$):</b> <code class="metric-ei">{ei_delta:.3f} мм</code></li>
                    <li><b>Допуск ($T_\Delta$):</b> <code>{tolerance_delta:.3f} мм</code></li>
                    <li><b>Максимальный предельный размер ($A_{{max}}$):</b> <code>{max_delta:.3f} мм</code></li>
                    <li><b>Минимальный предельный размер ($A_{{min}}$):</b> <code>{min_delta:.3f} мм</code></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with col_res_metrics:
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric(label="Номинал замыкающего звена AΔ", value=f"{nominal_delta:.3f} мм")
            if method == "Статистический анализ (Six Sigma)":
                st.metric(label="Выход годных (Yield %)", value=f"{yield_percent:.5f}%")
            else:
                st.metric(label="Поле допуска TΔ", value=f"{tolerance_delta:.3f} мм")
            
            # Кнопка для скачивания отчета
            report_text = f"""ОТЧЕТ ПО РАСЧЕТУ РАЗМЕРНОЙ ЦЕПИ
--------------------------------------
Режим расчета: {task_type}
Метод расчета: {method}
{"Параметры Six Sigma: Cp_детали=" + str(cp_detail) + ", Целевой уровень=" + str(quality_level) if method == "Статистический анализ (Six Sigma)" else ""}

СОСТАВЛЯЮЩИЕ ЗВЕНЬЯ:
{edited_df.to_string(index=False)}

РЕЗУЛЬТАТ (ЗАМЫКАЮЩЕЕ ЗВЕНО A_Delta):
Номинал: {nominal_delta:.3f} мм
Верхнее отклонение (ES): {es_delta:+.3f} мм
Нижнее отклонение (EI): {ei_delta:+.3f} мм
Допуск (T): {tolerance_delta:.3f} мм
Предельные размеры: [{min_delta:.3f} ... {max_delta:.3f}] мм
"""
            if method == "Статистический анализ (Six Sigma)":
                report_text += f"""
МЕТРИКИ КАЧЕСТКА (Six Sigma):
sigma сборки: {sigma_delta:.5f} мм
Уровень качества (Z-score): {z_score:.2f} Сигма
Индекс годности сборки Cp: {cp_assembly:.3f}
Yield (Выход годных): {yield_percent:.5f}%
Брак на миллион (PPM): {ppm:.1f}
"""

            st.download_button(
                label="📥 Скачать текстовый отчет",
                data=report_text,
                file_name="dimensional_chain_report.txt",
                mime="text/plain",
                use_container_width=True
            )

        # ==================== Отрисовка графика-колокола Гаусса ====================
        if method == "Статистический анализ (Six Sigma)" and sigma_delta > 0:
            st.markdown("---")
            st.subheader("📊 Распределение плотности вероятности замыкающего звена (Six Sigma)")
            
            fig_g, ax_g = plt.subplots(figsize=(12, 4.5))
            mean_val = (max_delta + min_delta) / 2.0
            
            x_pts = np.linspace(mean_val - 4.5 * sigma_delta, mean_val + 4.5 * sigma_delta, 1000)
            y_pts = (1.0 / (sigma_delta * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * ((x_pts - mean_val) / sigma_delta) ** 2)
            
            ax_g.plot(x_pts, y_pts, color="#1E3A8A", lw=2.5, label="Плотность распределения N(μ, σ²)")
            
            inside_mask = (x_pts >= min_delta) & (x_pts <= max_delta)
            ax_g.fill_between(x_pts[inside_mask], y_pts[inside_mask], color="#10B981", alpha=0.3, label=f"Годные (Yield: {yield_percent:.4f}%)")
            
            left_defect = x_pts < min_delta
            if np.any(left_defect):
                ax_g.fill_between(x_pts[left_defect], y_pts[left_defect], color="#EF4444", alpha=0.5, label="Зона брака (Выход за границы)")
            right_defect = x_pts > max_delta
            if np.any(right_defect):
                ax_g.fill_between(x_pts[right_defect], y_pts[right_defect], color="#EF4444", alpha=0.5)
                
            ax_g.axvline(x=min_delta, color="#EF4444", linestyle="--", lw=2, label=f"Нижняя граница ({min_delta:.3f})")
            ax_g.axvline(x=max_delta, color="#EF4444", linestyle="--", lw=2, label=f"Верхняя граница ({max_delta:.3f})")
            ax_g.axvline(x=mean_val, color="#1E3A8A", linestyle=":", lw=1.5, label=f"Центр распределения ({mean_val:.3f})")
            
            ax_g.set_xlabel("Размер замыкающего звена, мм", fontsize=10, fontweight="bold")
            ax_g.get_yaxis().set_visible(False)
            ax_g.spines['top'].set_visible(False)
            ax_g.spines['right'].set_visible(False)
            ax_g.spines['left'].set_visible(False)
            
            info_text = (
                f"σ сборки = {sigma_delta:.4f} мм\n"
                f"Z-score = {z_score:.2f}\n"
                f"Cp = {cp_assembly:.3f}\n"
                f"Брак = {ppm:.1f} PPM"
            )
            ax_g.text(
                0.02, 0.95, info_text, transform=ax_g.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='#D1D5DB')
            )
            
            ax_g.legend(loc="upper right", fontsize=9)
            st.pyplot(fig_g, bbox_inches='tight')

        # Раздел визуализации цепи (построение схемы векторов звеньев)
        st.markdown("---")
        st.subheader("🎨 Наглядная схема размерной цепи")
        
        num_links = len(edited_df)
        dynamic_height = max(4.5, 1.5 + 0.7 * num_links)
        
        fig, ax = plt.subplots(figsize=(12, dynamic_height))
        
        current_x = 0.0
        y_level = 0.5
        
        color_inc = "#3B82F6"
        color_dec = "#EF4444"
        color_delta = "#10B981"
        
        max_x_seen = 0.0
        min_x_seen = 0.0
        
        for idx, row in edited_df.iterrows():
            name = row["Название"]
            val = row["Номинал, мм"]
            is_inc = row["Tip"] == "Увеличивающее (+)" if "Tip" in row else row["Тип"] == "Увеличивающее (+)"
            
            dx = val if is_inc else -val
            color = color_inc if is_inc else color_dec
            
            label_suffix = " (К)" if "Компенсатор" in row and row["Компенсатор"] else ""
            
            ax.annotate(
                "", 
                xy=(current_x + dx, y_level), 
                xytext=(current_x, y_level),
                arrowprops=dict(arrowstyle="->", color=color, lw=2.5)
            )
            
            mid_point = current_x + dx / 2
            ax.text(
                mid_point, 
                y_level + 0.08, 
                f"{name}{label_suffix}\n({val:.2f})", 
                color=color, 
                ha='center', 
                va='bottom', 
                fontsize=9, 
                fontweight='bold'
            )
            
            ax.axvline(x=current_x, color="gray", linestyle="--", alpha=0.3, ymax=0.85, ymin=0.05)
            
            current_x += dx
            y_level += 0.3
            
            max_x_seen = max(max_x_seen, current_x, current_x - dx)
            min_x_seen = min(min_x_seen, current_x, current_x - dx)
        
        # Рисуем замыкающее звено
        ax.annotate(
            "", 
            xy=(nominal_delta, 0.2), 
            xytext=(0, 0.2),
            arrowprops=dict(arrowstyle="<->", color=color_delta, lw=3, ls="-")
        )
        
        ax.text(
            nominal_delta / 2, 
            0.28, 
            rf"$A_\Delta = {nominal_delta:.2f}$", 
            color=color_delta, 
            ha='center', 
            va='bottom', 
            fontsize=11, 
            fontweight='bold'
        )
        
        ax.axvline(x=0, color="black", linestyle="-", alpha=0.6, label="Начало отсчета (0)")
        ax.axvline(x=nominal_delta, color=color_delta, linestyle=":", alpha=0.8)
        
        ax.set_ylim(-0.2, y_level + 0.2)
        span = max_x_seen - min_x_seen if max_x_seen != min_x_seen else 10
        ax.set_xlim(min_x_seen - span * 0.1, max_x_seen + span * 0.1)
        
        ax.set_xlabel("Длина, мм", fontsize=11, fontweight='bold', labelpad=15)
        ax.get_yaxis().set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        from matplotlib.lines import Line2D
        custom_lines = [
            Line2D([0], [0], color=color_inc, lw=3, label='Увеличивающие звенья (+)'),
            Line2D([0], [0], color=color_dec, lw=3, label='Уменьшающие звенья (-)'),
            Line2D([0], [0], color=color_delta, lw=3, label='Замыкающее звено (Искомое)')
        ]
        ax.legend(
            handles=custom_lines, 
            loc='upper center', 
            bbox_to_anchor=(0.5, -0.2), 
            ncol=3, 
            frameon=True,
            fontsize=9
        )
        
        st.pyplot(fig, bbox_inches='tight')