import altair as alt
import pandas as pd
import streamlit as st
from vega_datasets import data

### Load Data ###
@st.cache_resource()
def load_data():
    covid_df = pd.read_csv('https://raw.githubusercontent.com/csjohnson23/BMI_706/main/post_covid_with_state_ids.csv')
    shortnames = pd.read_csv('https://raw.githubusercontent.com/csjohnson23/BMI_706/main/shortnames.tsv', sep='\t')
    covid_df = covid_df.merge(shortnames, how='left', on = ['Indicator'])
    return covid_df


def add_bg_from_url():
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("https://raw.githubusercontent.com/csjohnson23/BMI_706/main/Coronavirus_background_best.jpg");
             background-attachment: fixed;
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

add_bg_from_url()

df = load_data()
st.write('## Interrogation of Long Covid Incidence and Impact in the US Population')

### Claire ###
f1 = df

#### Data Set-Up
# Get state codes
pop = data.population_engineers_hurricanes()
pop = pop[['state', 'id']]
pop.columns = ['State', 'id']

f1 = f1[f1['Group'].isin(['By State', 'National Estimate'])]
f1 = f1[['Indicator', 'State', 'Time Period', 'Time Period Label', 'Value', 'LowCI', 'HighCI', 'Indicator_short']]
f1.columns = ['Indicator', 'State', 'Time Period Num', 'Time Period', 'Incidence (%)', 'LowCI', 'HighCI', 'Indicator_short']
f1 = f1.merge(pop, how = 'left', on = 'State')
f1.loc[f1['State'] == 'United States', 'id'] = 0

# Choose time period:
time_period = st.selectbox("Time Period: ", ('Jun 1 - Jun 13, 2022', 'Jun 29 - Jul 11, 2022',
       'Jul 27 - Aug 8, 2022', 'Aug 24 - Sep 13, 2022',
       'Sep 14 - Sep 26, 2022', 'Oct 5 - Oct 17, 2022',
       'Nov 2 - Nov 14, 2022', 'Nov 30 - Dec 8, 2022',
       'Dec 9 - Dec 19, 2022', 'Jan 4 - Jan 16, 2023',
       'Feb 1 - Feb 13, 2023'))

# Create panel-specific dfs
f1_bar = f1

f1_map = f1[f1['Indicator'] == 'Ever experienced long COVID, as a percentage of adults who ever had COVID']
f1_map = f1_map.sort_values('Incidence (%)', ascending = False)
f1_map['Rank'] = range(1, len(f1_map) + 1)

f1_map = f1_map[f1_map["Time Period"] == time_period]
f1_bar = f1_bar[f1_bar["Time Period"] == time_period]

#### Map
states = alt.topo_feature(data.us_10m.url, feature='states')
project = 'albersUsa'

background = alt.Chart(states
).mark_geoshape(
    fill='lightgray',
    stroke='white'
).project(project)

# Link visualizations: 
selector = alt.selection_single(empty='all', fields=['id'])
selector2 = alt.selection_single(empty='none', fields=['id'], init={'id':0})

chart_base = alt.Chart(states
    ).project(project
    ).add_selection(selector, selector2
    ).transform_lookup(
        lookup="id",
        from_=alt.LookupData(f1_map, "id", ["Incidence (%)", 'State', 'Rank', 'Time Period']),
    )
rate_scale = alt.Scale(domain=[f1_map['Incidence (%)'].min(), f1_map['Incidence (%)'].max()], scheme='oranges')
rate_color = alt.Color(field="Incidence (%)", type="quantitative", scale=rate_scale)

chart_rate = chart_base.mark_geoshape().encode(
    color = rate_color,
    tooltip = ['Incidence (%):Q', 'Rank:Q']
    ).transform_filter(
    selector
    ).properties(
    title='Long Covid Incidence Rates by State'
)


chart_details = alt.Chart(f1_bar).mark_bar().encode(
    y = alt.Y('Indicator_short:N', title = ''),
    x = alt.X('Incidence (%):Q', 
        scale=alt.Scale(domain=[0, 100])),
    tooltip=alt.Tooltip('Indicator_short:N', title=''),
    color = alt.value("#3D8789")
    ).transform_filter(
     selector2
).properties(
    title='Impact of Long Covid in Selected State'
)
f1_chart = alt.vconcat(background + chart_rate, chart_details
)

st.altair_chart(f1_chart, use_container_width=True)

### Grace ###
f2 = df.groupby(["Indicator_short", "Group", "Subgroup", "Value"], as_index=False).mean()

#### Heatmap
group_default = [
    "By Age"
]
groups = st.multiselect("Groups", list(f2['Group'].unique()), group_default)
subset = f2[f2["Group"].isin(groups)]

# Configure heatmap
chart2 = alt.Chart(subset).mark_rect().encode(
    y=alt.Y('Indicator_short:O', title=""),
    x=alt.X('Subgroup:O', title=""),
    color=alt.Color('Value:Q', title="Percent Response", scale=alt.Scale(scheme='teals')),
    tooltip=[alt.Tooltip('Indicator_short:O', title="Indicator"), alt.Tooltip('Value:Q', title="Percent Response")]
).facet(
    column=alt.Column('Group:O', title="", sort=groups)
).resolve_scale(
  x='independent'
).configure_axis(
    labelLimit=1000
)
st.altair_chart(chart2, use_container_width=True)

#####  Adrienne
f3 = df[df.Phase != (-1)]

demographic = st.selectbox("Demogrpahic Group: ", ('By Age', 'By Sex', 'By Gender identity',
         'By Sexual orientation', 'By Race/Hispanic ethnicity', 'By Education', 'By Disability status'))

f3_subset = f3[f3["Group"] == demographic]

selector3 = alt.selection_single(fields=['Subgroup'])

color = alt.condition(selector3,
                      alt.Color('Subgroup:N', legend=None),
                      alt.value('lightgray'))

line = alt.Chart(f3_subset).mark_line().encode(
    x= alt.X('Time Period End Date:T', axis = alt.Axis(format = ("%b %Y"), labelAngle= 270), title=''),
    y= alt.Y('Value', title = "Percentage"),
    color=color
).properties(
    width=150,
    height=250
)

band = alt.Chart(f3_subset).mark_area(opacity=0.33).encode(
    x='Time Period End Date:T',
    y= 'LowCI',
    y2= 'HighCI',
    color = color
).properties(
    width=250,
    height=250
)

legend = alt.Chart(f3_subset).mark_point().encode(
    y=alt.Y('Subgroup:N', axis=alt.Axis(orient='right')),
    color=color
).add_selection(
    selector3
)
chart3 = alt.layer(line, band, data=f3_subset).facet(
    facet = alt.Facet('Indicator_short:O', title=None), columns = 3).properties(
        title = "Percentage of responses over time").resolve_scale(
            y = "independent", x= "independent")

st.altair_chart(chart3 | legend, use_container_width=True)

st.write('Background creator: VectorStock.com/32170409 ')
