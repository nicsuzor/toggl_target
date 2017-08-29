from datetime import datetime
from yaml import load
from togglapi import api
from dateutil.relativedelta import relativedelta
import plotly


def main():

    try:
        with open("config.yml", 'r') as ymlfile:
            cfg = load(ymlfile)
    except:
        print("Unable to load config file.")
        exit()

    a = api.TogglAPI(cfg['toggl']['api_key'], cfg['toggl']['timezone'], useragent=cfg['toggl']['email'])

    plotly.tools.set_credentials_file(username=cfg['plotly']['username'], api_key=cfg['plotly']['api_key'])

    month_start = datetime.now() + relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)

    summary = a.get_summary(start_date=month_start, end_date=datetime.now(), workspace_id=cfg['toggl']['workspace'])

    chart_data = []

    for project in summary['data']:
        time = project['time'] / 1000 / 60 / 60
        total_time = sum(max(entry['time'], 0) for entry in project['items']) / 1000 / 60 / 60

        name = project['title']['project']

        if name and name.lower() in cfg['projects']:
            budget = cfg['projects'][name.lower()]

            trace = {'project': name, 'time': time, 'budget': budget}
            chart_data.append(trace)


    if chart_data:
        graph_charts(chart_data)

def graph_charts(chart_data):
    from plotly.offline import download_plotlyjs, plot, iplot

    import plotly.plotly as py
    import plotly.graph_objs as go

    traces = []

    y = []
    x_used = []
    x_free = []
    tooltip_used = []
    tooltip_free = []

    annotations = []

    for project in chart_data:
        time_used = project['time']
        budget = (project['budget'])
        proportion_used = time_used / budget
        y.append(project['project'])
        x_used.append(proportion_used)
        x_free.append(max(0, 1-proportion_used))
        tooltip_free.append('{0:.1f} hours remaining.'.format(max(0, budget-time_used)))
        if proportion_used >= 1:
            tooltip_used.append('Over budget! {0:.1f} hours used.'.format(time_used))
            annotations.append(dict(x=proportion_used, y=project['project'], text='<br>Over Budget!<br>{0:.1f} hours used.'.format(time_used),
                                    font=dict(family='Arial', size=14,
                                              color='rgba(0, 0, 0, 1)'),
                                    showarrow=False,
                                    textangle=90,
                                    xshift= -28,
                                    ))
        else:
            tooltip_used.append('{0:.1f} hours'.format(time_used))
            annotations.append(dict(x=proportion_used, y=project['project'], text='<br>{0:.1f} hours used'.format(time_used),
                                    font=dict(family='Arial', size=14,
                                              color='rgba(245, 246, 249, 1)'),
                                    showarrow=False,
                                    textangle=90,
                                    xshift= -14,
                                    ))
            annotations.append(dict(x=1, y=project['project'], text='<br>{0:.1f} hours free'.format(budget - time_used),
                                    font=dict(family='Arial', size=14,
                                              color='rgba(245, 246, 249, 1)'),
                                    showarrow=False,
                                    textangle=90,
                                    xshift= -14,
                                    ))

    trace_used = go.Bar(
        y = y,
        x = x_used,
        orientation='h',
        name = 'used',
        text = tooltip_used,
        hoverinfo = 'text',
        marker = dict(
            color = 'rgba(246, 78, 139, 0.6)',
            line = dict(
                color = 'rgba(246, 78, 139, 1.0)',
                width = 3)
        )
    )

    trace_free = go.Bar(
        y = y,
        x = x_free,
        orientation='h',
        name = 'free',
        hoverinfo='text+name',
        text=tooltip_free,
        marker = dict(
            color='rgba(58, 71, 80, 0.6)',
            line = dict(
                color = 'rgba(58, 71, 80, 1.0)',
                width = 3)
        )
    )



    traces = [trace_used, trace_free]

    layout = go.Layout(
        barmode='stack',
        title="Hours left this month",
        annotations = annotations,
        xaxis = dict(
            title='Proportion of time remaining'
        )
    )

    fig = go.Figure(data=traces, layout=layout)
    py.plot(fig, filename='timeleft')


if __name__ == '__main__':
    main()
