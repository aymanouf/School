import streamlit as st
import pandas as pd
import datetime
import json
import os
from decimal import Decimal
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Year 11 Committee Financial System",
    page_icon="💰",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

if 'budget' not in st.session_state:
    st.session_state.budget = {
        "income": {
            "Fundraising Events": {"budget": 0, "actual": 0},
            "Merchandise Sales": {"budget": 0, "actual": 0},
            "Sponsorships": {"budget": 0, "actual": 0},
            "Other Income": {"budget": 0, "actual": 0}
        },
        "expenses": {
            "Event Expenses": {"budget": 0, "actual": 0},
            "Merchandise Production": {"budget": 0, "actual": 0},
            "Marketing/Promotion": {"budget": 0, "actual": 0},
            "Yearbook": {"budget": 0, "actual": 0},
            "Graduation": {"budget": 0, "actual": 0},
            "School Trips": {"budget": 0, "actual": 0},
            "Emergency Reserve": {"budget": 0, "actual": 0},
            "Other Expenses": {"budget": 0, "actual": 0}
        }
    }

if 'events' not in st.session_state:
    st.session_state.events = []

if 'fundraising' not in st.session_state:
    st.session_state.fundraising = []

# Committee members
committee_members = {
    "Chair": "TBD",
    "Deputy Chair": "TBD",
    "Treasurer": "Deema Abououf",
    "Secretary": "TBD",
    "Events Coordinator": "TBD"
}

# Authorization levels based on the matrix
auth_levels = {
    "Under 100 KD": ["Chair"],
    "Over 100 KD": ["Chair", "School Admin"],
    "New Category": ["Committee Vote"]
}

# Helper functions
def get_balance():
    total_income = sum(t["income"] for t in st.session_state.transactions)
    total_expenses = sum(t["expense"] for t in st.session_state.transactions)
    return total_income - total_expenses

def get_emergency_reserve():
    # Calculate 15% of total income
    total_income = sum(t["income"] for t in st.session_state.transactions)
    return total_income * 0.15

def get_required_authorization(amount, category):
    # Check if this is a new category
    is_new_category = True
    for section in ["income", "expenses"]:
        if category in st.session_state.budget[section]:
            is_new_category = False
            break
    
    if is_new_category:
        return ["Committee Vote"]
    elif float(amount) > 100:
        return auth_levels["Over 100 KD"]
    else:
        return auth_levels["Under 100 KD"]

def add_transaction(date, description, category, income=0, expense=0, authorized_by="", receipt_num="", notes=""):
    # Validate transaction
    if not description or not category:
        return False, "Description and category are required"
    
    # Check authorization based on amount
    amount = max(income, expense)
    required_auth = get_required_authorization(amount, category)
    if authorized_by not in required_auth and "Committee Vote" not in required_auth:
        return False, f"This transaction requires authorization from: {', '.join(required_auth)}"
    
    # Add transaction
    transaction = {
        "date": date,
        "description": description,
        "category": category,
        "income": float(income),
        "expense": float(expense),
        "authorized_by": authorized_by,
        "receipt_num": receipt_num,
        "notes": notes,
        "timestamp": datetime.datetime.now().isoformat()
    }
    st.session_state.transactions.append(transaction)
    
    # Update budget actuals
    if income > 0:
        if category in st.session_state.budget["income"]:
            st.session_state.budget["income"][category]["actual"] += float(income)
        else:
            st.session_state.budget["income"]["Other Income"]["actual"] += float(income)
    
    if expense > 0:
        if category in st.session_state.budget["expenses"]:
            st.session_state.budget["expenses"][category]["actual"] += float(expense)
        else:
            st.session_state.budget["expenses"]["Other Expenses"]["actual"] += float(expense)
    
    return True, "Transaction added successfully"

def generate_monthly_report(month=None, year=None):
    now = datetime.datetime.now()
    month = month or now.month
    year = year or now.year
    
    # Filter transactions for the given month/year
    monthly_transactions = []
    for t in st.session_state.transactions:
        t_date = datetime.datetime.fromisoformat(t["timestamp"]).date()
        if t_date.month == month and t_date.year == year:
            monthly_transactions.append(t)
    
    monthly_income = sum(t["income"] for t in monthly_transactions)
    monthly_expenses = sum(t["expense"] for t in monthly_transactions)
    
    report = {
        "month": month,
        "year": year,
        "total_income": monthly_income,
        "total_expenses": monthly_expenses,
        "net": monthly_income - monthly_expenses,
        "transactions": monthly_transactions,
        "current_balance": get_balance(),
        "emergency_reserve": get_emergency_reserve(),
        "available_funds": get_balance() - get_emergency_reserve()
    }
    
    return report

def create_event_budget(event_name, date, location, coordinator, projected_income=0, projected_expenses=0):
    event = {
        "name": event_name,
        "date": date,
        "location": location,
        "coordinator": coordinator,
        "projected_income": float(projected_income),
        "projected_expenses": float(projected_expenses),
        "actual_income": 0,
        "actual_expenses": 0,
        "income_sources": [],
        "expense_items": [],
        "status": "Planning"  # Planning, Active, Completed
    }
    
    st.session_state.events.append(event)
    return True, "Event budget created successfully"

def add_fundraising_initiative(name, dates, coordinator, goal_amount):
    initiative = {
        "name": name,
        "dates": dates,
        "coordinator": coordinator,
        "goal_amount": float(goal_amount),
        "actual_raised": 0,
        "expenses": 0,
        "net_proceeds": 0,
        "status": "Planning"  # Planning, Active, Completed
    }
    
    st.session_state.fundraising.append(initiative)
    return True, "Fundraising initiative added successfully"

# Dashboard function
def show_dashboard():
    st.header("Financial Dashboard")
    
    # Summary cards in a row
    col1, col2, col3 = st.columns(3)
    
    balance = get_balance()
    reserve = get_emergency_reserve()
    available = balance - reserve
    
    with col1:
        st.metric("Current Balance", f"KD {balance:.2f}")
    
    with col2:
        st.metric("Emergency Reserve (15%)", f"KD {reserve:.2f}")
    
    with col3:
        st.metric("Available Funds", f"KD {available:.2f}")
    
    # Recent transactions
    st.subheader("Recent Transactions")
    
    if st.session_state.transactions:
        transactions_df = pd.DataFrame(st.session_state.transactions)
        # Sort by timestamp (newest first)
        transactions_df = transactions_df.sort_values(by="timestamp", ascending=False)
        # Limit to last 5
        recent_transactions = transactions_df.head(5)
        # Select only the columns we want to display
        display_columns = ["date", "description", "category", "income", "expense", "authorized_by"]
        st.dataframe(recent_transactions[display_columns], use_container_width=True)
    else:
        st.info("No transactions recorded yet.")
    
    # Budget overview with charts
    st.subheader("Budget Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Income budget vs actual
        income_data = []
        for category, values in st.session_state.budget["income"].items():
            income_data.append({
                "Category": category,
                "Budget": values["budget"],
                "Actual": values["actual"]
            })
        
        if income_data:
            income_df = pd.DataFrame(income_data)
            fig = px.bar(income_df, x="Category", y=["Budget", "Actual"], 
                        title="Income: Budget vs. Actual",
                        barmode="group",
                        color_discrete_sequence=["#1f77b4", "#2ca02c"])
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Expense budget vs actual
        expense_data = []
        for category, values in st.session_state.budget["expenses"].items():
            expense_data.append({
                "Category": category,
                "Budget": values["budget"],
                "Actual": values["actual"]
            })
        
        if expense_data:
            expense_df = pd.DataFrame(expense_data)
            fig = px.bar(expense_df, x="Category", y=["Budget", "Actual"], 
                        title="Expenses: Budget vs. Actual",
                        barmode="group",
                        color_discrete_sequence=["#d62728", "#ff7f0e"])
            st.plotly_chart(fig, use_container_width=True)
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Add Transaction", use_container_width=True):
            st.session_state.page = "transactions"
    
    with col2:
        if st.button("Generate Report", use_container_width=True):
            st.session_state.page = "reports"
    
    with col3:
        if st.button("Manage Budget", use_container_width=True):
            st.session_state.page = "budget"

# Transactions function
def show_transactions():
    st.header("Transactions Management")
    
    # Add new transaction form
    with st.expander("Add New Transaction", expanded=True):
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date", value=datetime.date.today())
                description = st.text_input("Description")
                
                # Get all categories
                categories = list(st.session_state.budget["income"].keys()) + list(st.session_state.budget["expenses"].keys())
                category = st.selectbox("Category", categories)
                
                income = st.number_input("Income (KD)", min_value=0.0, format="%.2f")
            
            with col2:
                expense = st.number_input("Expense (KD)", min_value=0.0, format="%.2f")
                
                # Get all possible authorizers
                authorizers = list(committee_members.keys()) + ["School Admin", "Committee Vote"]
                authorized_by = st.selectbox("Authorized By", authorizers)
                
                receipt_num = st.text_input("Receipt #")
                notes = st.text_area("Notes", height=100)
            
            submit = st.form_submit_button("Add Transaction")
            
            if submit:
                success, message = add_transaction(
                    date.strftime("%Y-%m-%d"),
                    description,
                    category,
                    income,
                    expense,
                    authorized_by,
                    receipt_num,
                    notes
                )
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # View transactions
    st.subheader("Transaction History")
    
    if st.session_state.transactions:
        transactions_df = pd.DataFrame(st.session_state.transactions)
        # Sort by date (newest first)
        transactions_df = transactions_df.sort_values(by="timestamp", ascending=False)
        # Format currency columns
        transactions_df["income"] = transactions_df["income"].apply(lambda x: f"KD {x:.2f}" if x > 0 else "")
        transactions_df["expense"] = transactions_df["expense"].apply(lambda x: f"KD {x:.2f}" if x > 0 else "")
        # Select columns to display
        display_columns = ["date", "description", "category", "income", "expense", "authorized_by", "receipt_num", "notes"]
        st.dataframe(transactions_df[display_columns], use_container_width=True)
        
        # Export option
        if st.button("Export Transactions to CSV"):
            csv = transactions_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="transactions.csv",
                mime="text/csv"
            )
    else:
        st.info("No transactions recorded yet.")

# Budget function
def show_budget():
    st.header("Budget Management")
    
    # Add new budget category
    with st.expander("Add New Budget Category"):
        with st.form("new_category_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                category_name = st.text_input("Category Name")
                category_type = st.radio("Category Type", ["Income", "Expenses"])
            
            with col2:
                initial_budget = st.number_input("Initial Budget (KD)", min_value=0.0, format="%.2f")
            
            submit = st.form_submit_button("Add Category")
            
            if submit:
                if not category_name:
                    st.error("Category name is required")
                else:
                    category_type = category_type.lower()
                    if category_type == "income":
                        if category_name in st.session_state.budget["income"]:
                            st.error(f"Category '{category_name}' already exists in income categories")
                        else:
                            st.session_state.budget["income"][category_name] = {"budget": initial_budget, "actual": 0}
                            st.success(f"Added '{category_name}' to income categories")
                    else:
                        if category_name in st.session_state.budget["expenses"]:
                            st.error(f"Category '{category_name}' already exists in expense categories")
                        else:
                            st.session_state.budget["expenses"][category_name] = {"budget": initial_budget, "actual": 0}
                            st.success(f"Added '{category_name}' to expense categories")
    
    # Adjust existing budget categories
    with st.expander("Adjust Budget Amounts"):
        st.subheader("Income Categories")
        
        for category, values in st.session_state.budget["income"].items():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.text(category)
            
            with col2:
                current_budget = values["budget"]
                st.text(f"Current: KD {current_budget:.2f}")
            
            with col3:
                new_budget = st.number_input(f"New budget for {category}", 
                                            min_value=0.0, 
                                            value=float(current_budget),
                                            key=f"income_{category}",
                                            format="%.2f")
                if new_budget != current_budget:
                    st.session_state.budget["income"][category]["budget"] = new_budget
        
        st.subheader("Expense Categories")
        
        for category, values in st.session_state.budget["expenses"].items():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.text(category)
            
            with col2:
                current_budget = values["budget"]
                st.text(f"Current: KD {current_budget:.2f}")
            
            with col3:
                new_budget = st.number_input(f"New budget for {category}", 
                                            min_value=0.0, 
                                            value=float(current_budget),
                                            key=f"expense_{category}",
                                            format="%.2f")
                if new_budget != current_budget:
                    st.session_state.budget["expenses"][category]["budget"] = new_budget
    
    # Budget overview
    st.subheader("Budget Summary")
    
    # Calculate totals
    total_income_budget = sum(values["budget"] for values in st.session_state.budget["income"].values())
    total_income_actual = sum(values["actual"] for values in st.session_state.budget["income"].values())
    total_expense_budget = sum(values["budget"] for values in st.session_state.budget["expenses"].values())
    total_expense_actual = sum(values["actual"] for values in st.session_state.budget["expenses"].values())
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Income Budget", f"KD {total_income_budget:.2f}")
    
    with col2:
        st.metric("Total Income Actual", f"KD {total_income_actual:.2f}", 
                 f"{(total_income_actual - total_income_budget):.2f}")
    
    with col3:
        st.metric("Total Expense Budget", f"KD {total_expense_budget:.2f}")
    
    with col4:
        st.metric("Total Expense Actual", f"KD {total_expense_actual:.2f}", 
                 f"{(total_expense_actual - total_expense_budget):.2f}")
    
    # Budget tables
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Income Budget")
        
        income_data = []
        for category, values in st.session_state.budget["income"].items():
            income_data.append({
                "Category": category,
                "Budget": f"KD {values['budget']:.2f}",
                "Actual": f"KD {values['actual']:.2f}",
                "Variance": f"KD {values['actual'] - values['budget']:.2f}",
                "% of Budget": f"{(values['actual'] / values['budget'] * 100):.1f}%" if values['budget'] > 0 else "N/A"
            })
        
        if income_data:
            income_df = pd.DataFrame(income_data)
            st.dataframe(income_df, use_container_width=True)
    
    with col2:
        st.subheader("Expense Budget")
        
        expense_data = []
        for category, values in st.session_state.budget["expenses"].items():
            expense_data.append({
                "Category": category,
                "Budget": f"KD {values['budget']:.2f}",
                "Actual": f"KD {values['actual']:.2f}",
                "Variance": f"KD {values['actual'] - values['budget']:.2f}",
                "% of Budget": f"{(values['actual'] / values['budget'] * 100):.1f}%" if values['budget'] > 0 else "N/A"
            })
        
        if expense_data:
            expense_df = pd.DataFrame(expense_data)
            st.dataframe(expense_df, use_container_width=True)
    
    # Budget visualization
    st.subheader("Budget Visualization")
    
    # Budget vs. Actual bar chart
    fig = go.Figure()
    
    # Add budget bars
    fig.add_trace(go.Bar(
        name='Income Budget',
        x=['Income'],
        y=[total_income_budget],
        marker_color='rgba(44, 160, 44, 0.7)'
    ))
    
    fig.add_trace(go.Bar(
        name='Income Actual',
        x=['Income'],
        y=[total_income_actual],
        marker_color='rgba(44, 160, 44, 1.0)'
    ))
    
    fig.add_trace(go.Bar(
        name='Expense Budget',
        x=['Expense'],
        y=[total_expense_budget],
        marker_color='rgba(214, 39, 40, 0.7)'
    ))
    
    fig.add_trace(go.Bar(
        name='Expense Actual',
        x=['Expense'],
        y=[total_expense_actual],
        marker_color='rgba(214, 39, 40, 1.0)'
    ))
    
    # Update layout
    fig.update_layout(
        title='Budget vs. Actual Summary',
        xaxis_title='Category',
        yaxis_title='Amount (KD)',
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Events function
def show_events():
    st.header("Event Management")
    
    # Add new event
    with st.expander("Create New Event Budget", expanded=True):
        with st.form("event_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                event_name = st.text_input("Event Name")
                event_date = st.date_input("Date")
                location = st.text_input("Location")
            
            with col2:
                coordinator = st.selectbox("Event Coordinator", list(committee_members.keys()))
                projected_income = st.number_input("Projected Income (KD)", min_value=0.0, format="%.2f")
                projected_expenses = st.number_input("Projected Expenses (KD)", min_value=0.0, format="%.2f")
            
            submit = st.form_submit_button("Create Event Budget")
            
            if submit:
                if not event_name or not event_date:
                    st.error("Event name and date are required")
                else:
                    success, message = create_event_budget(
                        event_name,
                        event_date.strftime("%Y-%m-%d"),
                        location,
                        coordinator,
                        projected_income,
                        projected_expenses
                    )
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    # View events
    st.subheader("Planned Events")
    
    if st.session_state.events:
        events_df = pd.DataFrame(st.session_state.events)
        # Format currency columns
        events_df["projected_income"] = events_df["projected_income"].apply(lambda x: f"KD {x:.2f}")
        events_df["projected_expenses"] = events_df["projected_expenses"].apply(lambda x: f"KD {x:.2f}")
        events_df["actual_income"] = events_df["actual_income"].apply(lambda x: f"KD {x:.2f}")
        events_df["actual_expenses"] = events_df["actual_expenses"].apply(lambda x: f"KD {x:.2f}")
        # Rename columns for display
        display_df = events_df.rename(columns={
            "name": "Event Name",
            "date": "Date",
            "location": "Location",
            "coordinator": "Coordinator",
            "projected_income": "Projected Income",
            "projected_expenses": "Projected Expenses",
            "actual_income": "Actual Income",
            "actual_expenses": "Actual Expenses",
            "status": "Status"
        })
        # Select columns to display
        display_columns = ["Event Name", "Date", "Location", "Coordinator", 
                          "Projected Income", "Projected Expenses", "Status"]
        st.dataframe(display_df[display_columns], use_container_width=True)
        
        # Event details
        st.subheader("Event Details")
        selected_event = st.selectbox("Select event to view details", 
                                     [e["name"] for e in st.session_state.events])
        
        if selected_event:
            event = next((e for e in st.session_state.events if e["name"] == selected_event), None)
            
            if event:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(event["name"])
                    st.write(f"**Date:** {event['date']}")
                    st.write(f"**Location:** {event['location']}")
                    st.write(f"**Coordinator:** {event['coordinator']}")
                    st.write(f"**Status:** {event['status']}")
                
                with col2:
                    # Financial summary
                    st.subheader("Financial Summary")
                    projected_profit = event["projected_income"] - event["projected_expenses"]
                    actual_profit = event["actual_income"] - event["actual_expenses"]
                    
                    st.write(f"**Projected Income:** KD {event['projected_income']:.2f}")
                    st.write(f"**Projected Expenses:** KD {event['projected_expenses']:.2f}")
                    st.write(f"**Projected Profit:** KD {projected_profit:.2f}")
                    st.write(f"**Actual Income:** KD {event['actual_income']:.2f}")
                    st.write(f"**Actual Expenses:** KD {event['actual_expenses']:.2f}")
                    st.write(f"**Actual Profit:** KD {actual_profit:.2f}")
                
                # Update event status
                new_status = st.selectbox("Update Status", 
                                         ["Planning", "Active", "Completed"],
                                         index=["Planning", "Active", "Completed"].index(event["status"]))
                
                if new_status != event["status"]:
                    event["status"] = new_status
                    st.success(f"Updated {event['name']} status to {new_status}")
                
                # Update actual figures
                with st.expander("Update Actual Figures"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_income = st.number_input("Actual Income (KD)", 
                                                   min_value=0.0, 
                                                   value=float(event["actual_income"]),
                                                   format="%.2f")
                    
                    with col2:
                        new_expenses = st.number_input("Actual Expenses (KD)", 
                                                     min_value=0.0, 
                                                     value=float(event["actual_expenses"]),
                                                     format="%.2f")
                    
                    if st.button("Update Figures"):
                        event["actual_income"] = new_income
                        event["actual_expenses"] = new_expenses
                        st.success("Updated actual figures")
    else:
        st.info("No events created yet.")

# Reports function
def show_reports():
    st.header("Financial Reports")
    
    # Report type selection
    report_type = st.radio("Report Type", 
                          ["Monthly Summary", "Year-to-Date", "Event Analysis", "Fundraising Results"],
                          horizontal=True)
    
    if report_type == "Monthly Summary":
        # Month and year selection
        col1, col2 = st.columns(2)
        
        with col1:
            month_names = [
                "January", "February", "March", "April", "May", "June", 
                "July", "August", "September", "October", "November", "December"
            ]
            selected_month = st.selectbox("Month", month_names)
            month_index = month_names.index(selected_month) + 1
        
        with col2:
            current_year = datetime.datetime.now().year
            selected_year = st.selectbox("Year", 
                                        list(range(current_year-2, current_year+3)))
        
        # Generate report
        if st.button("Generate Report"):
            report = generate_monthly_report(month_index, selected_year)
            
            # Display report
            st.subheader(f"Monthly Financial Report - {selected_month} {selected_year}")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Income", f"KD {report['total_income']:.2f}")
            
            with col2:
                st.metric("Total Expenses", f"KD {report['total_expenses']:.2f}")
            
            with col3:
                st.metric("Net", f"KD {report['net']:.2f}")
            
            # Overall financial position
            st.subheader("Overall Financial Position")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Balance", f"KD {report['current_balance']:.2f}")
            
            with col2:
                st.metric("Emergency Reserve", f"KD {report['emergency_reserve']:.2f}")
            
            with col3:
                st.metric("Available Funds", f"KD {report['available_funds']:.2f}")
            
            # Transactions
            st.subheader("Transactions")
            
            if report['transactions']:
                transactions_df = pd.DataFrame(report['transactions'])
                # Format currency columns
                transactions_df["income"] = transactions_df["income"].apply(lambda x: f"KD {x:.2f}" if x > 0 else "")
                transactions_df["expense"] = transactions_df["expense"].apply(lambda x: f"KD {x:.2f}" if x > 0 else "")
                # Select columns to display
                display_columns = ["date", "description", "category", "income", "expense", "authorized_by"]
                st.dataframe(transactions_df[display_columns], use_container_width=True)
            else:
                st.info("No transactions for this period.")
    
    elif report_type == "Year-to-Date":
        # Year selection
        current_year = datetime.datetime.now().year
        selected_year = st.selectbox("Year", 
                                    list(range(current_year-2, current_year+3)))
        
        # Generate report
        if st.button("Generate Report"):
            # Collect data for each month
            now = datetime.datetime.now()
            end_month = now.month if selected_year == now.year else 12
            
            monthly_data = []
            total_income = 0
            total_expenses = 0
            
            for month in range(1, end_month + 1):
                report = generate_monthly_report(month, selected_year)
                monthly_data.append({
                    "month": month,
                    "income": report["total_income"],
                    "expenses": report["total_expenses"],
                    "net": report["net"]
                })
                total_income += report["total_income"]
                total_expenses += report["total_expenses"]
            
            # Display report
            st.subheader(f"Year-to-Date Financial Report - {selected_year}")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Income YTD", f"KD {total_income:.2f}")
            
            with col2:
                st.metric("Total Expenses YTD", f"KD {total_expenses:.2f}")
            
            with col3:
                st.metric("Net YTD", f"KD {total_income - total_expenses:.2f}")
            
            # Monthly breakdown
            st.subheader("Monthly Breakdown")
            
            if monthly_data:
                # Create DataFrame
                month_names = [
                    "January", "February", "March", "April", "May", "June", 
                    "July", "August", "September", "October", "November", "December"
                ]
                
                for data in monthly_data:
                    data["month_name"] = month_names[data["month"]-1]
                
                monthly_df = pd.DataFrame(monthly_data)
                monthly_df["income"] = monthly_df["income"].apply(lambda x: f"KD {x:.2f}")
                monthly_df["expenses"] = monthly_df["expenses"].apply(lambda x: f"KD {x:.2f}")
                monthly_df["net"] = monthly_df["net"].apply(lambda x: f"KD {x:.2f}")
                
                display_df = monthly_df.rename(columns={
                    "month_name": "Month",
                    "income": "Income",
                    "expenses": "Expenses",
                    "net": "Net"
                })
                
                st.dataframe(display_df[["Month", "Income", "Expenses", "Net"]], use_container_width=True)
                
                # Chart
                chart_df = pd.DataFrame(monthly_data)
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=chart_df["month_name"],
                    y=chart_df["income"],
                    name="Income",
                    marker_color="rgba(44, 160, 44, 0.8)"
                ))
                
                fig.add_trace(go.Bar(
                    x=chart_df["month_name"],
                    y=chart_df["expenses"],
                    name="Expenses",
                    marker_color="rgba(214, 39, 40, 0.8)"
                ))
                
                fig.add_trace(go.Scatter(
                    x=chart_df["month_name"],
                    y=chart_df["net"],
                    name="Net",
                    mode="lines+markers",
                    line=dict(color="rgba(31, 119, 180, 1.0)", width=3)
                ))
                
                fig.update_layout(
                    title=f"Monthly Financial Performance - {selected_year}",
                    xaxis_title="Month",
                    yaxis_title="Amount (KD)",
                    legend_title="Category"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for this year.")
    
    elif report_type == "Event Analysis":
        if not st.session_state.events:
            st.info("No events available for analysis.")
        else:
            # Event selection
            selected_event = st.selectbox("Select Event", 
                                         [e["name"] for e in st.session_state.events])
            
            # Generate report
            if st.button("Generate Report"):
                event = next((e for e in st.session_state.events if e["name"] == selected_event), None)
                
                if event:
                    # Display report
                    st.subheader(f"Event Analysis Report - {event['name']}")
                    
                    # Event details
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Date:** {event['date']}")
                        st.write(f"**Location:** {event['location']}")
                        st.write(f"**Coordinator:** {event['coordinator']}")
                        st.write(f"**Status:** {event['status']}")
                    
                    # Financial analysis
                    st.subheader("Financial Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Income:**")
                        st.write(f"Projected: KD {event['projected_income']:.2f}")
                        st.write(f"Actual: KD {event['actual_income']:.2f}")
                        variance = event['actual_income'] - event['projected_income']
                        st.write(f"Variance: KD {variance:.2f} ({variance/event['projected_income']*100:.1f}% of projection)" if event['projected_income'] > 0 else "Variance: N/A")
                    
                    with col2:
                        st.write("**Expenses:**")
                        st.write(f"Projected: KD {event['projected_expenses']:.2f}")
                        st.write(f"Actual: KD {event['actual_expenses']:.2f}")
                        variance = event['actual_expenses'] - event['projected_expenses']
                        st.write(f"Variance: KD {variance:.2f} ({variance/event['projected_expenses']*100:.1f}% of projection)" if event['projected_expenses'] > 0 else "Variance: N/A")
                    
                    st.write("**Net:**")
                    projected_profit = event['projected_income'] - event['projected_expenses']
                    actual_profit = event['actual_income'] - event['actual_expenses']
                    st.write(f"Projected Profit: KD {projected_profit:.2f}")
                    st.write(f"Actual Profit: KD {actual_profit:.2f}")
                    profit_variance = actual_profit - projected_profit
                    st.write(f"Profit Variance: KD {profit_variance:.2f}")
                    
                    # Visualization
                    fig = go.Figure()
                    
                    categories = ["Income", "Expenses", "Profit"]
                    projected = [event['projected_income'], event['projected_expenses'], projected_profit]
                    actual = [event['actual_income'], event['actual_expenses'], actual_profit]
                    
                    fig.add_trace(go.Bar(
                        x=categories,
                        y=projected,
                        name="Projected",
                        marker_color="rgba(31, 119, 180, 0.8)"
                    ))
                    
                    fig.add_trace(go.Bar(
                        x=categories,
                        y=actual,
                        name="Actual",
                        marker_color="rgba(255, 127, 14, 0.8)"
                    ))
                    
                    fig.update_layout(
                        title=f"Financial Performance - {event['name']}",
                        xaxis_title="Category",
                        yaxis_title="Amount (KD)",
                        legend_title="Type",
                        barmode="group"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    
    elif report_type == "Fundraising Results":
        if not st.session_state.fundraising:
            st.info("No fundraising initiatives available for analysis.")
        else:
            # Calculate total results
            total_goal = sum(f["goal_amount"] for f in st.session_state.fundraising)
            total_raised = sum(f["actual_raised"] for f in st.session_state.fundraising)
            total_expenses = sum(f["expenses"] for f in st.session_state.fundraising)
            total_net = sum(f["net_proceeds"] for f in st.session_state.fundraising)
            
            # Display report
            st.subheader("Fundraising Results Report")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Goal", f"KD {total_goal:.2f}")
            
            with col2:
                st.metric("Total Raised", f"KD {total_raised:.2f}")
            
            with col3:
                st.metric("Total Expenses", f"KD {total_expenses:.2f}")
            
            with col4:
                st.metric("Total Net Proceeds", f"KD {total_net:.2f}")
            
            if total_goal > 0:
                st.metric("Overall Success Rate", f"{(total_raised/total_goal)*100:.1f}%")
            
            # Individual initiatives
            st.subheader("Individual Initiatives")
            
            if st.session_state.fundraising:
                fundraising_df = pd.DataFrame(st.session_state.fundraising)
                # Calculate success rate
                fundraising_df["success_rate"] = fundraising_df.apply(
                    lambda x: f"{(x['actual_raised']/x['goal_amount'])*100:.1f}%" if x['goal_amount'] > 0 else "N/A", 
                    axis=1
                )
                # Format currency columns
                fundraising_df["goal_amount"] = fundraising_df["goal_amount"].apply(lambda x: f"KD {x:.2f}")
                fundraising_df["actual_raised"] = fundraising_df["actual_raised"].apply(lambda x: f"KD {x:.2f}")
                fundraising_df["expenses"] = fundraising_df["expenses"].apply(lambda x: f"KD {x:.2f}")
                fundraising_df["net_proceeds"] = fundraising_df["net_proceeds"].apply(lambda x: f"KD {x:.2f}")
                # Rename columns for display
                display_df = fundraising_df.rename(columns={
                    "name": "Initiative Name",
                    "dates": "Dates",
                    "coordinator": "Coordinator",
                    "goal_amount": "Goal",
                    "actual_raised": "Raised",
                    "expenses": "Expenses",
                    "net_proceeds": "Net Proceeds",
                    "success_rate": "Success Rate",
                    "status": "Status"
                })
                # Select columns to display
                display_columns = ["Initiative Name", "Dates", "Coordinator", 
                                  "Goal", "Raised", "Expenses", "Net Proceeds", 
                                  "Success Rate", "Status"]
                st.dataframe(display_df[display_columns], use_container_width=True)

# Fundraising function
def show_fundraising():
    st.header("Fundraising Management")
    
    # Add new fundraising initiative
    with st.expander("Add New Fundraising Initiative", expanded=True):
        with st.form("fundraising_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Initiative Name")
                dates = st.text_input("Dates (e.g., Apr 15-20)")
            
            with col2:
                coordinator = st.selectbox("Coordinator", list(committee_members.keys()))
                goal_amount = st.number_input("Goal Amount (KD)", min_value=0.0, format="%.2f")
            
            submit = st.form_submit_button("Add Initiative")
            
            if submit:
                if not name:
                    st.error("Initiative name is required")
                else:
                    success, message = add_fundraising_initiative(
                        name,
                        dates,
                        coordinator,
                        goal_amount
                    )
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    # View fundraising initiatives
    st.subheader("Fundraising Initiatives")
    
    if st.session_state.fundraising:
        fundraising_df = pd.DataFrame(st.session_state.fundraising)
        # Format currency columns
        fundraising_df["goal_amount"] = fundraising_df["goal_amount"].apply(lambda x: f"KD {x:.2f}")
        fundraising_df["actual_raised"] = fundraising_df["actual_raised"].apply(lambda x: f"KD {x:.2f}")
        fundraising_df["expenses"] = fundraising_df["expenses"].apply(lambda x: f"KD {x:.2f}")
        fundraising_df["net_proceeds"] = fundraising_df["net_proceeds"].apply(lambda x: f"KD {x:.2f}")
        # Rename columns for display
        display_df = fundraising_df.rename(columns={
            "name": "Initiative Name",
            "dates": "Dates",
            "coordinator": "Coordinator",
            "goal_amount": "Goal Amount",
            "actual_raised": "Amount Raised",
            "expenses": "Expenses",
            "net_proceeds": "Net Proceeds",
            "status": "Status"
        })
        # Select columns to display
        display_columns = ["Initiative Name", "Dates", "Coordinator", 
                          "Goal Amount", "Amount Raised", "Status"]
        st.dataframe(display_df[display_columns], use_container_width=True)
        
        # Initiative details
        st.subheader("Initiative Details")
        selected_initiative = st.selectbox("Select initiative to view details", 
                                         [f["name"] for f in st.session_state.fundraising])
        
        if selected_initiative:
            initiative = next((f for f in st.session_state.fundraising if f["name"] == selected_initiative), None)
            
            if initiative:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(initiative["name"])
                    st.write(f"**Dates:** {initiative['dates']}")
                    st.write(f"**Coordinator:** {initiative['coordinator']}")
                    st.write(f"**Status:** {initiative['status']}")
                
                with col2:
                    # Financial summary
                    st.subheader("Financial Summary")
                    st.write(f"**Goal Amount:** KD {initiative['goal_amount']:.2f}")
                    st.write(f"**Amount Raised:** KD {initiative['actual_raised']:.2f}")
                    st.write(f"**Expenses:** KD {initiative['expenses']:.2f}")
                    st.write(f"**Net Proceeds:** KD {initiative['net_proceeds']:.2f}")
                    
                    if initiative['goal_amount'] > 0:
                        success_rate = (initiative['actual_raised'] / initiative['goal_amount']) * 100
                        st.write(f"**Success Rate:** {success_rate:.1f}%")
                
                # Update initiative status
                new_status = st.selectbox("Update Status", 
                                         ["Planning", "Active", "Completed"],
                                         index=["Planning", "Active", "Completed"].index(initiative["status"]))
                
                if new_status != initiative["status"]:
                    initiative["status"] = new_status
                    st.success(f"Updated {initiative['name']} status to {new_status}")
                
                # Update actual figures
                with st.expander("Update Actual Figures"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_raised = st.number_input("Amount Raised (KD)", 
                                                   min_value=0.0, 
                                                   value=float(initiative["actual_raised"]),
                                                   format="%.2f")
                    
                    with col2:
                        new_expenses = st.number_input("Expenses (KD)", 
                                                     min_value=0.0, 
                                                     value=float(initiative["expenses"]),
                                                     format="%.2f")
                    
                    if st.button("Update Figures"):
                        initiative["actual_raised"] = new_raised
                        initiative["expenses"] = new_expenses
                        initiative["net_proceeds"] = new_raised - new_expenses
                        st.success("Updated actual figures")
    else:
        st.info("No fundraising initiatives created yet.")

# Save and load functions
def save_data():
    data = {
        "budget": st.session_state.budget,
        "transactions": st.session_state.transactions,
        "events": st.session_state.events,
        "fundraising": st.session_state.fundraising
    }
    
    # Convert to JSON
    json_data = json.dumps(data, indent=4)
    
    # Provide download link
    st.download_button(
        label="Download Data Backup",
        data=json_data,
        file_name="financial_system_backup.json",
        mime="application/json"
    )
    
    st.success("Data prepared for download")

def load_data():
    uploaded_file = st.file_uploader("Upload backup file", type=["json"])
    
    if uploaded_file:
        # Read the file
        data = json.load(uploaded_file)
        
        # Update session state
        st.session_state.budget = data.get("budget", st.session_state.budget)
        st.session_state.transactions = data.get("transactions", st.session_state.transactions)
        st.session_state.events = data.get("events", st.session_state.events)
        st.session_state.fundraising = data.get("fundraising", st.session_state.fundraising)
        
        st.success("Data loaded successfully")
        st.experimental_rerun()

# Main app
def main():
    # Sidebar navigation
    st.sidebar.title("Year 11 Committee")
    st.sidebar.subheader("Financial Management System")
    
    # Set default page if not exists
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # Navigation
    page = st.sidebar.radio("Navigation", 
                           ["Dashboard", "Transactions", "Budget", "Events", 
                            "Fundraising", "Reports", "Settings"],
                           index=["dashboard", "transactions", "budget", "events", 
                                 "fundraising", "reports", "settings"].index(st.session_state.page))
    
    # Store the current page
    st.session_state.page = page.lower()
    
    # Display the selected page
    if st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'transactions':
        show_transactions()
    elif st.session_state.page == 'budget':
        show_budget()
    elif st.session_state.page == 'events':
        show_events()
    elif st.session_state.page == 'fundraising':
        show_fundraising()
    elif st.session_state.page == 'reports':
        show_reports()
    elif st.session_state.page == 'settings':
        st.header("Settings")
        
        # Save/Load data
        st.subheader("Data Backup and Restore")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Save current data to a file:")
            if st.button("Prepare Backup File"):
                save_data()
        
        with col2:
            st.write("Load data from a backup file:")
            load_data()
            
    # Display footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Developed by Deema Abououf\n\n"
        "Treasurer/Finance Manager\n"
        "Year 11 Committee"
    )

if __name__ == '__main__':
    main()
