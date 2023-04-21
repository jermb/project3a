import pygal, re, requests
from datetime import datetime, timedelta
from pygal.style import Style

__key__ = "ZJHR7RBL4JVUMUO5"

class Graph:

    def __init__(self, symbol: str, graph_type: str, time_series: str, 
                 start_date: str = None, end_date: str = None):
        self.symbol = symbol
        self.graph_type = graph_type
        self.time_series = time_series
        self.start_date = start_date
        self.end_date = end_date    

        self.api_call()

    def create(self):
        '''
            Creates a graph from the given data and displays it in the user's default browser.

            Parameters:
                json: A dictionary representation of the data JSON.
                graph: A pygal graph object (pygal.Bar() & pygal.Line() are known to work)
        '''

        graph = pygal.Line() if self.graph_type == "line" else pygal.Bar()
        dates = []
        options = { "Open": [], "High": [], "Low": [], "Close": [] }

        #   Creates a function to format the dates properly
        datetime = self.string_to_datetime()

        #   Formats data from JSON to be used by graph
        for item in self.data:
            dates.append(datetime(item["date"]))
            options["Open"].append(float(item["1. open"]))
            options["High"].append(float(item["2. high"]))
            options["Low"].append(float(item["3. low"]))
            options["Close"].append(float(item["4. close"]))

        if self.start_date == "":
            self.start_date = dates[0]
        if self.end_date == "":
            self.end_date = dates[len(dates) - 1]

        #   Add data and labels to graph
        for opt in options: graph.add(opt, options[opt])
        graph.x_labels = dates
        graph.title = self.title()

        #   Styles the graph
        graph_styling(graph, len(dates))

        #   Renders the graph as an SVG in the user's default browser
        return graph.render_data_uri()


    def api_call(self):
        '''
            Creates an api call using the given parameters

            Parameters:
                symbol: Stock symbol as string
                time_series: formatted time series string

            Returns:
                dictionary representation of api response
        '''
        #   Add interval parameter for intraday requests
        interval = "&interval=15min" if self.time_series == "TIME_SERIES_INTRADAY" else ""
        #   Create api call url
        url = f"https://www.alphavantage.co/query?function={self.time_series}&symbol={self.symbol}{interval}&apikey={__key__}"
        #   Parse the response data from json to a dictionary and return
        self.data = self.extract_data(requests.get(url).json())


    def extract_data(self, json: dict):
        '''
            Reformats the JSON response into an array containing each data point as a self contained dictionary.

            Parameters:
                json: A dictionary representing the response from the API

            Returns:
                Array of the newly minted data points. list[dict[str, Any]]
        '''
        #   Finds the "Time Series" key within the dictionary, whether it is "Time Series (Daily)", "... (Monthly)", or "... (15min)"
        #   Loops through keys, checks if they match, then will return the first (and only) instance
        try:
            time_series = [k for k in json.keys() if re.match(r".*Time Series.*", k)][0]
        except IndexError:
            raise ValueError("Could not find data for this query")

        #   Takes each line that looks like this: "YYYY-MM-DD": {"key1": "value1", "key2": "value2"}
        #   Converts it to this {"date": "YYYY-MM-DD", "key1": "value1", "key2": "value2"}
        #   And places them all into a list
        data_points = [{"date": k, **v} for k, v in json[time_series].items()]

        #   Sorts the list using the get_date function and returns it
        data_points.sort(key = get_date)

        #   Finds index of Begin Date and End date
        start = self.get_date_index(data_points, self.start_date)
        end = self.get_date_index(data_points, self.end_date)

        #   Gets the data between the given dates
        return segment_data(data_points, start, end)

    
    def get_date_index(self, data: list, date: str):
        '''
            Finds the index of the item with the given data

            Parameters:
                data: list of all data points
                date: string representing date to be searched for in formate YYYY-MM-DD

            Returns:
                int representing index of the item in the list OR -1 to represent the date not existing
        '''
        #   Allows date to be empty
        if date == "": return -1

        #   If it is weekly data try to find a date near the requested date
        if (self.time_series == "TIME_SERIES_WEEKLY"):
            date: datetime = datetime.strptime(date, "%Y-%m-%d")
            dates = [date]
            for i in range(-3,4):
                week_day = (date + timedelta(days=i)).strftime("%Y-%m-%d")
                print(week_day)
                for k in range(len(data)):
                    if week_day in data[k]["date"]:
                        return k
            return -1

        #   If monthly only check the month and year fields
        if (self.time_series == "TIME_SERIES_MONTHLY"):
            date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")

        #   Iterate through data to find index of date in data
        for i in range(len(data)):
            if date in data[i]["date"]:
                return i
        return -1
    

    def string_to_datetime(self):
        '''
            Returns the convert() function:

            Standard Function:
                Converts a string date in format YYYY-MM-DD

            Function for Intraday Graphs:
                Converts string date to foramt HH:MM:SS
                Keeps track what calendar date the data points belong to. When a data point exists on a new day the label is changed to YYYY-MM-DD HH:MM:SS to avoid confusion.

            Parameters:
                date: String date in format YYYY-MM-DD w/ optional time formatting HH:MM:SS

            Returns:
                string 
        '''
        #   Set the previous var to be an impossible value so it can be used without messing with the graph.
        previous = datetime(1, 1, 1)

        def convert(date: str):
            #   Stores the previous day as a static variable
            nonlocal previous

            if (self.time_series == "TIME_SERIES_INTRADAY"):
                #   For Intraday graphs:
                day = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                if (day.date() == previous.date()):
                    #   Format the date as HH:MM:SS
                    format = '%H:%M:%S'
                else:
                    #   Unless the data point is the start of a new day
                    #   In that case format as YY-MM-DD HH:MM:SS
                    format = '%Y-%m-%d %H:%M:%S'
                    previous = day

                return day.strftime(format)
            else:
                #   For all other graph types, format is YYYY-MM-DD
                return datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
        return convert


    def title(self):
        return f"Stock Data for {self.symbol}: {self.start_date} to {self.end_date}"
    

##############################
#####  Helper functions  #####
##############################


def get_date(item: dict):
    '''
        Gets the value of "date" from a dictionary (used for sorting)
    '''
    return item["date"]

def segment_data(data:list, start:int, end:int) -> list:
    '''
        Retrieves the segement of the data between two index points

        Parameters:
            data: the list of the dictionary data points

    '''
    start = start if start != -1 else 0
    end = end if end != -1 else len(data)
    return [data[i] for i in range(start, end)]

def graph_styling(graph: pygal.Graph, point_count: int):
    '''
        Adds styling to the graph object. It has no bearing on the functions of the program, only the readability of the final graph.

        Parameters:
            graph: a pygal graph
            point_count: an int representing the number of data points on the graph
    '''
    #   Make larger graphs more readable
    if (point_count > 100):
        graph.x_labels_major_every = 10
        graph.show_minor_x_labels = False

    #   Many elements use the number of points on the graph to make elements proportional.
    graph.style = Style(
        label_font_size = point_count/3,
        major_label_font_size = point_count/3,
        stroke_width = 15,
        legend_font_size = point_count/2,
        title_font_size = point_count,
        tooltip_font_size = point_count/3
    )
    graph.dots_size = 15
    graph.x_label_rotation = 90
    graph.width = point_count * 50
    graph.height = point_count * 25 
    graph.legend_box_size = point_count/3


def check_dates(start:str, end:str) -> bool:
    '''
        Checks whether the dates given by the user give a valid range where the start does not come after the end.

        If either date is empty the return is True

        Parameters:
            start, end: string reperesentations of dates in the format YYYY-MM-DD

        Returns:
            bool
    '''
    if start == "" or end == "":
        return True

    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    return start < end