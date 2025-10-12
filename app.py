from flask import Flask, request, render_template, jsonify, send_file, session, redirect, url_for
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = 'uploads'
GRAPH_FOLDER = 'static/graphs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GRAPH_FOLDER'] = GRAPH_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GRAPH_FOLDER, exist_ok=True)

# Updated Graph Types
GRAPH_TYPES = ['histogram', 'line', 'scatter', 'box', 'violin', 'density']

@app.route('/')
def index():
    return render_template('index.html', graph_types=GRAPH_TYPES)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    session['csv_filepath'] = filepath

    return redirect(url_for('results'))

@app.route('/results', methods=['GET', 'POST'])
def results():
    if 'csv_filepath' not in session:
        return redirect(url_for('index'))

    filepath = session['csv_filepath']
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {str(e)}"}), 500

    graph_type = request.form.get('graph_type', 'histogram')
    graph_paths = generate_graphs(df, graph_type)

    session['last_graph_type'] = graph_type
    session['graph_paths'] = graph_paths

    # Generate summary statistics
    summary = df.describe().to_html(classes="table table-striped table-bordered")

    return render_template('results.html', graphs=graph_paths, graph_type=graph_type, summary=summary)

def generate_graphs(df, graph_type):
    graph_paths = []
    max_graphs = min(len(df.columns), 7)

    for column in df.columns[:max_graphs]:
        graph_path = os.path.join(app.config['GRAPH_FOLDER'], f"{column}_{graph_type}.png")

        plt.figure(figsize=(8, 5))
        plt.xlabel(column)
        plt.ylabel("Frequency")

        try:
            if graph_type == 'histogram':
                sns.histplot(df[column], bins=20, kde=True)
                plt.title(f"{column} - Histogram")

            elif graph_type == 'line':
                sns.lineplot(data=df[column])
                plt.title(f"{column} - Line Chart")

            elif graph_type == 'scatter' and len(df.columns) > 1:
                plt.scatter(df.iloc[:, 0], df[column])
                plt.xlabel(df.columns[0])
                plt.ylabel(column)
                plt.title(f"{df.columns[0]} vs {column} - Scatter Plot")

            elif graph_type == 'box':
                sns.boxplot(y=df[column])
                plt.title(f"{column} - Box Plot")

            elif graph_type == 'violin':
                sns.violinplot(y=df[column])
                plt.title(f"{column} - Violin Plot")

            
            
            elif graph_type == 'density':
                sns.kdeplot(df[column], fill=True)
                plt.title(f"{column} - Density Plot")

            plt.savefig(graph_path)
            plt.close()
            graph_paths.append(graph_path)

        except Exception as e:
            print(f"Error generating {graph_type} for {column}: {str(e)}")

    return graph_paths

@app.route('/analyze_data', methods=['GET'])
def analyze_data():
    if 'csv_filepath' not in session:
        return jsonify({"error": "⚠️ No data uploaded. Please upload a CSV first."}), 400

    filepath = session['csv_filepath']
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return jsonify({"error": f"⚠️ Error reading CSV: {str(e)}"}), 500

    insights = generate_detailed_insights(df)
    return jsonify({"insights": insights})

def generate_detailed_insights(df):
    insights = []
    
    # Page Views Insights
    if 'Page Views' in df.columns:
        avg_views = df['Page Views'].mean()
        if avg_views > 10000:
            insights.append(f"🌟 **Excellent Engagement!** Your site receives an **average of {avg_views:.2f} views per session**, showing high user interest. Keep up the great work!")
        elif 5000 <= avg_views <= 10000:
            insights.append(f"📈 **Good Engagement!** The average views per session are **{avg_views:.2f}**, indicating a decent audience reach. Consider content optimization for further improvement.")
        else:
            insights.append(f"📉 **Low Engagement!** The average views per session are **{avg_views:.2f}**, which suggests low interest. Enhance SEO and social media promotion.")

    # Bounce Rate Insights
    if 'Bounce Rate' in df.columns:
        avg_bounce = df['Bounce Rate'].mean()
        if avg_bounce > 60:
            insights.append(f"⚠️ **Very High Bounce Rate!** At **{avg_bounce:.2f}%**, most visitors leave quickly. Improve page loading speed and optimize content.")
        elif 40 <= avg_bounce <= 60:
            insights.append(f"⚠️ **Moderate Bounce Rate!** At **{avg_bounce:.2f}%**, some visitors leave early. Consider better CTAs and engaging design.")
        else:
            insights.append(f"✅ **Great Bounce Rate!** At **{avg_bounce:.2f}%**, visitors are interacting well with your content.")

    # Session Duration Insights
    if 'Session Duration' in df.columns:
        avg_duration = df['Session Duration'].mean()
        if avg_duration > 180:
            insights.append(f"⏳ **Excellent User Engagement!** Visitors stay for an **average of {avg_duration:.2f} seconds**, indicating valuable content.")
        elif 90 <= avg_duration <= 180:
            insights.append(f"📊 **Moderate Session Duration!** Visitors spend **{avg_duration:.2f} seconds** on your site. Try adding interactive content to increase engagement.")
        else:
            insights.append(f"🚀 **Short Sessions!** The average session duration is **{avg_duration:.2f} seconds**. Improve content structure and add visuals.")

    # Traffic Source Insights
    if 'Traffic Source' in df.columns:
        top_source = df['Traffic Source'].mode()[0]
        insights.append(f"🌍 **Majority of Traffic Comes From:** **{top_source}**. Optimize marketing strategies for this channel.")

    # Time on Page Insights
    if 'Time on Page' in df.columns:
        avg_time_on_page = df['Time on Page'].mean()
        if avg_time_on_page > 120:
            insights.append(f"📖 **Users Spend Time on Pages!** The average time on page is **{avg_time_on_page:.2f} seconds**, indicating useful content.")
        elif 60 <= avg_time_on_page <= 120:
            insights.append(f"⏱️ **Moderate Time on Page!** The average time spent is **{avg_time_on_page:.2f} seconds**. Improve content engagement.")
        else:
            insights.append(f"⚡ **Users Leave Quickly!** The average time on page is **{avg_time_on_page:.2f} seconds**. Improve readability and add engaging elements.")

    # Previous Visits Insights
    if 'Previous Visits' in df.columns:
        avg_previous_visits = df['Previous Visits'].mean()
        if avg_previous_visits > 3:
            insights.append(f"🔄 **Loyal Visitors!** The average returning visitor count is **{avg_previous_visits:.2f}**, showing strong user retention.")
        elif 1 <= avg_previous_visits <= 3:
            insights.append(f"🆕 **Some Returning Visitors!** The average is **{avg_previous_visits:.2f}**. Consider adding membership benefits or loyalty programs.")
        else:
            insights.append(f"📢 **Mostly New Visitors!** With **{avg_previous_visits:.2f} previous visits**, focus on retaining users.")

    # Conversion Rate Insights
    if 'Conversion Rate' in df.columns:
        avg_conversion = df['Conversion Rate'].mean()
        if avg_conversion > 5:
            insights.append(f"🎯 **Great Conversion Rate!** At **{avg_conversion:.2f}%**, your site effectively turns visitors into customers.")
        elif 2 <= avg_conversion <= 5:
            insights.append(f"📊 **Moderate Conversion Rate!** At **{avg_conversion:.2f}%**, some improvements could be made in marketing strategies.")
        else:
            insights.append(f"🚀 **Low Conversion Rate!** With **{avg_conversion:.2f}%**, optimize landing pages and enhance CTAs.")

    # Default message if no insights are found
    if not insights:
        insights.append("⚠️ **No insights available.** Ensure your data includes all required fields.")

    return insights

 
@app.route('/download_graph_type_report')
def download_graph_type_report():
    if 'graph_paths' not in session or 'last_graph_type' not in session or 'csv_filepath' not in session:
        return redirect(url_for('index'))

    graph_paths = session['graph_paths']
    graph_type = session['last_graph_type']
    filepath = session['csv_filepath']

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {str(e)}"}), 500

    insights = generate_detailed_insights(df)
    summary_stats = df.describe().to_string()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # PDF Title
    pdf.cell(200, 10, f"Site Metrics Report - {graph_type.capitalize()}", ln=True, align='C')
    pdf.ln(10)

    # Insights Section (No Emojis)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Key Insights", ln=True)
    pdf.set_font("Arial", size=10)
    for insight in insights:
        pdf.multi_cell(0, 10, insight.encode('latin-1', 'ignore').decode('latin-1'))
    pdf.ln(10)

    # Summary Statistics (Avoid Unicode Issues)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Data Summary", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, summary_stats.encode('latin-1', 'ignore').decode('latin-1'))
    pdf.ln(10)

    # Graphs Section
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Graphs", ln=True)
    pdf.ln(5)

    for graph in graph_paths:
        pdf.image(graph, x=10, w=150)
        pdf.ln(10)

    report_path = os.path.join(app.config['GRAPH_FOLDER'], f"{graph_type}_report.pdf")
    pdf.output(report_path, "F")  # Force writing file

    return send_file(report_path, as_attachment=True)

@app.route('/download_complete_report')
def download_complete_report():
    if 'csv_filepath' not in session:
        return redirect(url_for('index'))

    filepath = session['csv_filepath']
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {str(e)}"}), 500

    all_graph_paths = []
    for graph_type in GRAPH_TYPES:
        all_graph_paths.extend(generate_graphs(df, graph_type))

    insights = generate_detailed_insights(df)
    summary_stats = df.describe().to_string()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # PDF Title
    pdf.cell(200, 10, "Site Metrics - Complete Report", ln=True, align='C')
    pdf.ln(10)

    # Key Insights (No Emojis)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Key Insights", ln=True)
    pdf.set_font("Arial", size=10)
    for insight in insights:
        pdf.multi_cell(0, 10, insight.encode('latin-1', 'ignore').decode('latin-1'))
    pdf.ln(10)

    # Data Summary
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Data Summary", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, summary_stats.encode('latin-1', 'ignore').decode('latin-1'))
    pdf.ln(10)

    # Graphs Section
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Graphs", ln=True)
    pdf.ln(5)

    for graph in all_graph_paths:
        if os.path.exists(graph):
            pdf.image(graph, x=10, w=150)
            pdf.ln(10)

    report_path = os.path.join(app.config['GRAPH_FOLDER'], "Complete_Site_Metrics_Report.pdf")
    pdf.output(report_path, "F")

    return send_file(report_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
