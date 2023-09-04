import sys
from PyQt5.QtWidgets import QDialog, QFileDialog, QApplication, QProgressBar, QTextEdit, QHBoxLayout, QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem, QWidget,  \
    QComboBox, \
    QLabel, QLineEdit, QPushButton, QAbstractItemView, QTabWidget, QMessageBox
from PyQt5.QtCore import Qt, QRegExp, QTimer
from PyQt5.QtGui import QTextCharFormat, QSyntaxHighlighter, QFont
import psycopg2
from datetime import datetime
import pandas as pd


class CustomMessageBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login Successful")

        layout = QVBoxLayout()

        opening_message = QLabel()
        opening_message.setStyleSheet("""
            QLabel {
                font-size: 14px;
                margin-bottom: 10px;
            }
        """)
        opening_message.setTextFormat(Qt.RichText)
        opening_message.setText("This app was created by <strong>Alper Aşınmaz</strong> for the <em>Kaymakçı Archaeological Project</em> in <strong>2023</strong>.")
        layout.addWidget(opening_message)

        self.loading_bar = QProgressBar()
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #fff;
                color: #000;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        self.loading_bar.setMinimum(0)
        self.loading_bar.setMaximum(100)
        layout.addWidget(self.loading_bar)

        self.setLayout(layout)

    def update_loading_bar(self, progress):
        self.loading_bar.setValue(progress)

class LoginWindow(QDialog):
    def __init__(self, db_name, db_user, db_password, db_host, db_port):
        super().__init__()

        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

        self.username = None


        self.setWindowTitle("Login")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add username label and text field
        username_label = QLabel("Username:")
        self.username_textfield = QLineEdit()
        self.username_textfield.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout.addWidget(username_label)
        layout.addWidget(self.username_textfield)

        # Add password label and text field
        password_label = QLabel("Password:")
        self.password_textfield = QLineEdit()
        self.password_textfield.setEchoMode(QLineEdit.Password)
        self.password_textfield.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout.addWidget(password_label)
        layout.addWidget(self.password_textfield)

        # Add login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(login_button)

    def login(self):
        username = self.username_textfield.text()
        password = self.password_textfield.text()
        self.username = username
        self.password = password  # Store the entered password

        try:
            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Execute the query to fetch usernames and passwords
            cursor.execute("SELECT name, password FROM public.survey_team_members")
            rows = cursor.fetchall()

            # Check if the entered username and password match any row in the database
            for row in rows:
                if row[0] == username and row[1] == password:
                    success_dialog = CustomMessageBox(self)

                    timer = QTimer(self)
                    progress = 0

                    def update_loading_bar():
                        nonlocal progress
                        if progress <= 100:
                            success_dialog.update_loading_bar(progress)
                            progress += 1
                        else:
                            timer.stop()
                            success_dialog.close()

                    timer.timeout.connect(update_loading_bar)
                    timer.start(30)  # Update every 50 milliseconds

                    success_dialog.exec_()  # Show the custom message dialog
                    self.accept()  # Login successful, accept the dialog
                    break
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password")

                # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving usernames and passwords from PostgreSQL:", error)
            QMessageBox.critical(self, "Error", f"Error retrieving usernames and passwords:\n{error}")


class DatabaseViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PostgreSQL Table Viewer")
        self.setGeometry(200, 200, 800, 600)

        # Store the database connection details
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

        # Database connection settings
        self.db_name = "your database nameb"
        self.db_user = "user names"
        self.db_password = "password"
        self.db_host = "localhost"
        self.db_port = "5432" #default



        # Create the main layout
        layout = QVBoxLayout()

        # Create the tab widget
        self.tab_widget = QTabWidget()

        # Add the tab widget to the main layout
        layout.addWidget(self.tab_widget)

        # Set the main layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect to the database and populate the table dropdown
        self.populate_table_dropdown()

        # Create the location tab
        location_tab = LocationTab("database_name", "user_name", "password", "localhost", "5432", username)

        self.tab_widget.addTab(location_tab, "Location Tab")

        # Create the SQL Query tab
        sql_query_tab = SQLQueryTab(db_name, db_user, db_password, db_host, db_port)
        self.tab_widget.addTab(sql_query_tab, "SQL Queries")

    def populate_table_dropdown(self):
        try:
            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Execute a query to fetch table names
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()

            # Populate the table dropdown
            for table in tables:
                self.table_dropdown.addItem(table[0])

            # Populate the name dropdown
            self.populate_name_dropdown()

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving table names from PostgreSQL:", error)

    def populate_coordinate_dropdown(self):
        try:
            # Clear the coordinate dropdown
            self.coordinate_dropdown.clear()

            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Get the selected table from the dropdown
            selected_table = self.table_dropdown.currentText()

            # Execute a query to fetch distinct values from both "area_easting" and "area_northing" columns
            cursor.execute(f"SELECT DISTINCT area_easting, area_northing FROM {selected_table}")
            coordinate_values = cursor.fetchall()

            # Combine and populate the coordinate dropdown with distinct values from both columns
            for value in coordinate_values:
                combined_value = f"{value[0]}, {value[1]}"
                self.coordinate_dropdown.addItem(combined_value)

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving coordinate values from PostgreSQL:", error)

    def populate_name_dropdown(self):
        try:
            # Clear the name dropdown
            self.name_dropdown.clear()

            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Execute a query to fetch the distinct values from the "name" column of the "public.survey_team_members" table
            cursor.execute("SELECT DISTINCT name FROM public.survey_team_members")
            names = cursor.fetchall()

            # Populate the name dropdown
            for name in names:
                self.name_dropdown.addItem(name[0])

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving survey team member names from PostgreSQL:", error)

    def load_table_contents(self):
        try:
            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Get the selected table from the dropdown
            selected_table = self.table_dropdown.currentText()

            # Get the selectedcoordinate value from the dropdown
            selected_coordinate = self.coordinate_dropdown.currentText()

            # Split the selected coordinate value into easting and northing values
            selected_coordinate_parts = selected_coordinate.split(", ")
            selected_easting = selected_coordinate_parts[0]
            selected_northing = selected_coordinate_parts[1]

            # Get the filter values from the text boxes
            context_filter = self.context_filter_textbox.text()
            sample_filter = self.sample_filter_textbox.text()
            name_filter = self.name_dropdown.currentText()

            # Update the record count textbox
            self.record_count_textbox.setText(f"Record Count: {self.table_widget.rowCount()}")

            # Build the SQL query with optional filters
            query = f"SELECT * FROM {selected_table} WHERE area_easting = '{selected_easting}' AND area_northing = '{selected_northing}'"
            if context_filter:
                query += f" AND context_number = '{context_filter}'"
            if sample_filter:
                query += f" AND sample_number = '{sample_filter}'"

            # Execute the query
            cursor.execute(query)
            rows = cursor.fetchall()

            # Get column names
            column_names = [desc[0] for desc in cursor.description]

            # Set table properties
            self.table_widget.setColumnCount(len(column_names))
            self.table_widget.setHorizontalHeaderLabels(column_names)
            self.table_widget.setRowCount(len(rows))

            # Populate table with data
            for row_index, row_data in enumerate(rows):
                for col_index, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    self.table_widget.setItem(row_index, col_index, item)

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving data from PostgreSQL:", error)


class LocationTab(QWidget):
    def __init__(self, db_name, db_user, db_password, db_host, db_port, username):
        super().__init__()

        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.username = username

        # Define selected_rows attribute
        self.selected_rows = set()

        # Create the layout for the location tab
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create the username label and textbox
        username_label = QLabel("Current User:")

        self.username_textbox = QLineEdit()
        self.username_textbox.setReadOnly(True)
        self.username_textbox.setText(self.username)
        layout.addWidget(username_label)
        layout.addWidget(self.username_textbox)
        self.username_textbox.setStyleSheet("background-color: grey; color: white; bold;")

        # Create the dropdown widget for table selection with default value
        self.table_dropdown = QComboBox()
        self.table_dropdown.addItem("storage_app")  # Set default value
        self.table_dropdown.currentIndexChanged.connect(self.load_table_contents)
        layout.addWidget(self.table_dropdown)

        # Create the dropdown widget for current_location selection
        self.current_location_dropdown = QComboBox()
        self.current_location_dropdown.currentIndexChanged.connect(self.load_table_contents)
        layout.addWidget(self.current_location_dropdown)

        # Create the filter dropdown for area_easting and area_northing
        self.area_filter_label = QLabel("Filter Area:")
        layout.addWidget(self.area_filter_label)
        self.area_filter_dropdown = QComboBox()
        self.area_filter_dropdown.currentIndexChanged.connect(self.load_table_contents)
        layout.addWidget(self.area_filter_dropdown)

        # Connect to the database and populate the area filter dropdown
        self.populate_area_filter_dropdown()

        # Create the filter textbox for context_number
        self.context_filter_label = QLabel("Context Number:")
        layout.addWidget(self.context_filter_label)
        self.context_filter_textbox = QLineEdit()
        self.context_filter_textbox.textChanged.connect(self.load_table_contents)
        layout.addWidget(self.context_filter_textbox)

        # Create the filter textbox for sample_number
        self.sample_filter_label = QLabel("Sample Number:")
        layout.addWidget(self.sample_filter_label)
        self.sample_filter_textbox = QLineEdit()
        self.sample_filter_textbox.textChanged.connect(self.load_table_contents)
        layout.addWidget(self.sample_filter_textbox)

        # Connect to the database and populate the dropdowns
        self.populate_table_dropdown()
        self.populate_current_location_dropdown()

        # Create the filter textbox for rack
        self.rack_filter_label = QLabel("Filter Rack:")
        layout.addWidget(self.rack_filter_label)
        self.rack_filter_textbox = QLineEdit()
        self.rack_filter_textbox.textChanged.connect(self.load_table_contents)
        layout.addWidget(self.rack_filter_textbox)

        # Create the filter textbox for shelf
        self.shelf_filter_label = QLabel("Filter Shelf:")
        layout.addWidget(self.shelf_filter_label)
        self.shelf_filter_textbox = QLineEdit()
        self.shelf_filter_textbox.textChanged.connect(self.load_table_contents)
        layout.addWidget(self.shelf_filter_textbox)

        # Create the filter textbox for container
        self.container_filter_label = QLabel("Filter Container:")
        layout.addWidget(self.container_filter_label)
        self.container_filter_textbox = QLineEdit()
        self.container_filter_textbox.textChanged.connect(self.load_table_contents)
        layout.addWidget(self.container_filter_textbox)

        # Create the table widget
        self.table_widget = QTableWidget()
        self.table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Enable multiple row selection
        self.table_widget.itemSelectionChanged.connect(self.update_selected_items)  # Connect selection change signal
        layout.addWidget(self.table_widget)

        # Create the rack update textbox
        self.rack_update_label = QLabel("Update Rack:")
        layout.addWidget(self.rack_update_label)
        self.rack_update_textbox = QLineEdit()
        layout.addWidget(self.rack_update_textbox)

        # Create the shelf update textbox
        self.shelf_update_label = QLabel("Update Shelf:")
        layout.addWidget(self.shelf_update_label)
        self.shelf_update_textbox = QLineEdit()
        layout.addWidget(self.shelf_update_textbox)

        # Create the container update textbox
        self.container_update_label = QLabel("Update Container:")
        layout.addWidget(self.container_update_label)
        self.container_update_textbox = QLineEdit()
        layout.addWidget(self.container_update_textbox)

        # Create the update button
        self.update_button = QPushButton("Update Rack, Shelf, and Container")
        self.update_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.update_button.setEnabled(False)  # Disable initially
        self.update_button.clicked.connect(self.update_selected_records)
        layout.addWidget(self.update_button)

        # Create the update location dropdown
        self.location_update_label = QLabel("Update Location:")
        layout.addWidget(self.location_update_label)
        self.location_update_dropdown = QComboBox()
        layout.addWidget(self.location_update_dropdown)
        self.populate_location_dropdown()

        # Create the update location button
        self.update_location_button = QPushButton("Update Location")
        self.update_location_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.update_location_button.setEnabled(True)  # Disable initially
        self.update_location_button.clicked.connect(lambda: self.update_location(self.update_location_button))
        layout.addWidget(self.update_location_button)

        # Create a horizontal layout for the record count label and textbox
        record_count_layout = QHBoxLayout()

        # Create the record count label
        self.record_count_label = QLabel("Number of Records:")
        self.record_count_label.setStyleSheet("color: black; font-size: 12px; text-align: center;")

        # Create the record count textbox (read-only)
        self.record_count_textbox = QLineEdit()
        self.record_count_textbox.setReadOnly(True)
        self.record_count_textbox.setStyleSheet("color: black; font-size: 12px; text-align: center;")

        # Add the label and textbox to the horizontal layout
        record_count_layout.addWidget(self.record_count_label)
        record_count_layout.addWidget(self.record_count_textbox)

        # Add the record count layout to the main layout
        layout.addLayout(record_count_layout)

        # Update the record count textbox
        self.update_record_count()

        # Create the selected record count textbox (read-only)
        self.selected_record_count_textbox = QLineEdit()
        self.selected_record_count_textbox.setReadOnly(True)
        layout.addWidget(self.selected_record_count_textbox)

        # Connect selection change signal to the method
        self.table_widget.itemSelectionChanged.connect(self.update_selected_record_count)

    def populate_location_dropdown(self):
        try:
            # Clear the location dropdown
            self.location_update_dropdown.clear()

            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Execute the query to fetch the "current_location" column values
            cursor.execute("SELECT current_location FROM options.sample_current_location")
            locations = cursor.fetchall()

            # Populate the location dropdown
            for location in locations:
                self.location_update_dropdown.addItem(location[0])

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving locations from PostgreSQL:", error)

    def update_selected_record_count(self):
        selected_count = len(self.selected_rows)
        self.selected_record_count_textbox.setText(f"Selected Records: {selected_count}")

        # Change the background color of the textbox to red
        self.selected_record_count_textbox.setStyleSheet("background-color: red; color: white; font-weight: bold;")

    def populate_area_filter_dropdown(self):
        try:
            # Clear the area filter dropdown
            self.area_filter_dropdown.clear()
            # Add an option for no area filtering
            self.area_filter_dropdown.addItem("")

            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Execute the query to fetch the merged values of area_easting and area_northing columns
            cursor.execute(
                "SELECT area_easting || ', ' || area_northing FROM public.sde_excavation_areas WHERE status='active'")
            areas = cursor.fetchall()

            # Populate the area filter dropdown
            for area in areas:
                self.area_filter_dropdown.addItem(area[0])

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving areas from PostgreSQL:", error)

    def update_location(self, button):
        try:
            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Get the selected table from the dropdown
            selected_table = self.table_dropdown.currentText()

            # Get the new location value from the dropdown
            new_location = self.location_update_dropdown.currentText()

            # Get the current location filter value from the dropdown
            current_location_filter = self.current_location_dropdown.currentText()

            # Check if the new location is 'Depot'
            if new_location == 'Depot':
                # Get the new rack, shelf, and container values from the respective textboxes
                new_rack = self.rack_update_textbox.text()
                new_shelf = self.shelf_update_textbox.text()
                new_container = self.container_update_textbox.text()

                # Check if any of the required fields are empty
                if not new_rack or not new_shelf or not new_container:
                    QMessageBox.warning(self, "Error",
                                        "Rack, Shelf, and Container values are required for 'Depot' location.")
                    return
            else:
                new_rack = 'NULL'
                new_shelf = 'NULL'
                new_container = 'NULL'

            # Get the area filter value from the dropdown
            #  area_filter = self.area_filter_dropdown.currentText()

            # Iterate over the selected rows and update the location, rack, shelf, and container values
            for row in self.selected_rows:
                # Get the current context and sample values for the selected row
                area_easting_listed  = self.table_widget.item(row, 0).text()
                area_northing_listed = self.table_widget.item(row, 1).text()
                context_filter = self.table_widget.item(row, 2).text()
                sample_filter = self.table_widget.item(row, 3).text()

                # Build the SQL query with the selected row's filters, current location filter, area filter, and updated values
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                query = f"UPDATE {selected_table} SET " \
                        f"location = '{new_location}', " \
                        f"rack = {new_rack}, " \
                        f"shelf = {new_shelf}, " \
                        f"container = {new_container}, " \
                        f"timestamp = '{current_timestamp}', " \
                        f"person = '{self.username}' " \
                        f"WHERE context_number = '{context_filter}' " \
                        f"AND sample_number = '{sample_filter}' " \
                        f"AND location = '{current_location_filter}' " \
                        f"AND area_easting = '{area_easting_listed}'" \
                        f"AND area_northing = '{area_northing_listed}'" \

                # Execute the query
                cursor.execute(query)

            # Commit the changes
            connection.commit()

            # Close the cursor and database connection
            cursor.close()
            connection.close()

            # Update the table contents
            self.load_table_contents()



        except (Exception, psycopg2.Error) as error:
            print("Error updating location in PostgreSQL:", error)
            # Show error message
            QMessageBox.critical(self, "Error", f"Error updating location:\n{error}")
            # Enable the button again after error
            button.setEnabled(True)

    def update_selected_records(self):
        try:
            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Get the selected table from the dropdown
            selected_table = self.table_dropdown.currentText()

            # Get the new rack, shelf, and container values from the respective textboxes
            new_rack = self.rack_update_textbox.text()
            new_shelf = self.shelf_update_textbox.text()
            new_container = self.container_update_textbox.text()



            # Get the current timestamp
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update the rack, shelf, container, and person values for each selected row
            for row in self.selected_rows:
                # Get the current context and sample values for the selected row
                context_filter = self.table_widget.item(row, 2).text()
                sample_filter = self.table_widget.item(row, 3).text()

                # Build the SQL query with the selected row's filters and updated values
                query = (
                    f"UPDATE {selected_table} SET "
                    f"rack = '{new_rack}', "
                    f"shelf = '{new_shelf}', "
                    f"container = '{new_container}', "
                    f"person = '{self.username}', "
                    f"timestamp = '{current_timestamp}' "
                    f"WHERE context_number = '{context_filter}' "
                    f"AND sample_number = '{sample_filter}' "
                    f"AND area_easting = '{self.table_widget.item(row, 0).text()}' "
                    f"AND area_northing = '{self.table_widget.item(row, 1).text()}'"
                )

                # Execute the query
                cursor.execute(query)

            # Commit the changes
            connection.commit()

            # Close the database connection
            cursor.close()
            connection.close()

            # Update the table contents
            self.load_table_contents()

            # Show success message
            QMessageBox.information(self, "Success", "Rack, shelf, container, and person update successful!")

        except (Exception, psycopg2.Error) as error:
            print("Error updating rack, shelf, container, and person in PostgreSQL:", error)
            # Show error message
            QMessageBox.critical(self, "Error", f"Error updating rack, shelf, container, and person:\n{error}")

    def update_selected_items(self):
        self.selected_rows = set(index.row() for index in self.table_widget.selectedIndexes())

        location_selected = any(
            'location' in self.table_widget.horizontalHeaderItem(col).text().lower() for col in
            range(self.table_widget.columnCount())
        )

        self.update_button.setEnabled(bool(self.selected_rows) and location_selected)

    def populate_table_dropdown(self):
        try:
            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Execute a query to fetch table names
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()

            # Populate the table dropdown
            for table in tables:
                self.table_dropdown.addItem(table[0])

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving table names from PostgreSQL:", error)

    def populate_current_location_dropdown(self):
        try:
            # Clear the current_location dropdown
            self.current_location_dropdown.clear()

            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Execute a query to fetch distinct values from the "current_location" column
            cursor.execute("SELECT DISTINCT current_location FROM public.samples_samples")
            locations = cursor.fetchall()

            # Populate the current_location dropdown
            for location in locations:
                self.current_location_dropdown.addItem(location[0])

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving current_location values from PostgreSQL:", error)

    def load_table_contents(self):
        try:
            # Clear the table widget
            self.table_widget.clear()

            # Connect to the database
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Get the selected table from the dropdown
            selected_table = self.table_dropdown.currentText()

            # Get the area filter value from the dropdown
            area_filter = self.area_filter_dropdown.currentText()

            # Get the context filter value from the textbox
            context_filter = self.context_filter_textbox.text()

            # Get the sample filter value from the textbox
            sample_filter = self.sample_filter_textbox.text()

            # Get the rack filter value from the textbox
            rack_filter = self.rack_filter_textbox.text()

            # Get the shelf filter value from the textbox
            shelf_filter = self.shelf_filter_textbox.text()

            # Get the container filter value from the textbox
            container_filter = self.container_filter_textbox.text()

            # Get the selected location value from the dropdown
            selected_location = self.current_location_dropdown.currentText()

            # Build the SQL query with optional filters
            query = f"SELECT * FROM {selected_table}"
            filters = []
            if context_filter:
                filters.append(f"context_number = '{context_filter}'")
            if sample_filter:
                filters.append(f"sample_number = '{sample_filter}'")
            if rack_filter:
                filters.append(f"rack = '{rack_filter}'")
            if shelf_filter:
                filters.append(f"shelf = '{shelf_filter}'")
            if container_filter:
                filters.append(f"container = '{container_filter}'")
            if selected_location:
                filters.append(f"location = '{selected_location}'")
            if area_filter:
                filters.append(f"area_easting || ', ' || area_northing = '{area_filter}'")

            if filters:
                query += " WHERE " + " AND ".join(filters)

            # Execute the query to fetch the table contents
            cursor.execute(query)
            rows = cursor.fetchall()

            # Get column names
            column_names = [desc[0] for desc in cursor.description]

            # Set table properties
            self.table_widget.setColumnCount(len(column_names) if column_names else 0)

            self.table_widget.setHorizontalHeaderLabels(column_names)
            self.table_widget.setRowCount(len(rows))

            # After populating the table widget, update the record count
            self.update_record_count()

            # Populate table with data
            for row_index, row_data in enumerate(rows):
                for col_index, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    self.table_widget.setItem(row_index, col_index, item)

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error retrieving data from PostgreSQL:", error)

    def update_record_count(self):
        record_count = self.table_widget.rowCount()
        self.record_count_textbox.setText(str(record_count))

class SQLSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.blue)
        keyword_format.setFontWeight(QFont.Bold)

        self.highlighting_rules = [
            (QRegExp(r'\b(?:SELECT|select)\b|\b(?:FROM|from)\b|\b(?:WHERE|where)\b|\b(?:INSERT|insert)\b|\b(?:UPDATE|update)\b|\b(?:DELETE|delete)\b|\b(?:=|is|IS|NULL|null)\b|\b(?:ORDER|order|id|ASC|asc|DESC|desc|AND|and)\b'r'\b(?:SELECT|select)\b|\b(?:FROM|from)\b|\b(?:WHERE|where)\b|\b(?:INSERT|insert)\b|\b(?:UPDATE|update)\b|\b(?:DELETE|delete)\b|\b(?:=|is|IS|NULL|null)\b|\b(?:ORDER|order|id|ASC|asc|DESC|desc|AND|and|BY|by)\b'), keyword_format)
        ]

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class SQLQueryTab(QWidget):
    def __init__(self, db_name, db_user, db_password, db_host, db_port):
        super().__init__()

        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port


        # Create the layout for the SQL query tab
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create the SQL query input textbox
        self.query_textbox = QTextEdit()
        # Set the style for the query_textbox
        self.query_textbox.setStyleSheet(
            "background-color: lightgrey; font-weight: bold; font-size: 14px;"
        )
        # Apply syntax highlighting to the query_textbox
        self.highlighter = SQLSyntaxHighlighter(self.query_textbox.document())

        layout.addWidget(self.query_textbox)

        # Create the execute button
        execute_button = QPushButton("Execute Query")
        execute_button.setStyleSheet("background-color: #4CAF50; color: white;")
        execute_button.clicked.connect(self.execute_query)
        layout.addWidget(execute_button)

        # Create the result table widget
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        # Create the record count label
        self.record_count_label = QLabel()
        layout.addWidget(self.record_count_label)

        # Create the export button
        export_button = QPushButton("Export to Excel")
        export_button.setStyleSheet("background-color: #FF5733; color: white;")
        export_button.clicked.connect(self.export_to_excel)
        layout.addWidget(export_button)

    def execute_query(self):
        query = self.query_textbox.toPlainText()

        # Check if the query contains certain restricted keywords
        restricted_keywords = ['INSERT', 'UPDATE', 'DELETE']
        if any(keyword in query.upper() for keyword in restricted_keywords):
            QMessageBox.warning(self, "Restricted Query", "INSERT, UPDATE, and DELETE queries are not allowed!")
            return

        try:
            # Connect to the database and execute the query (if it's not restricted)
            connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            cursor = connection.cursor()

            # Execute the query
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

            # Populate the result table with data
            self.result_table.setColumnCount(len(column_names))
            self.result_table.setHorizontalHeaderLabels(column_names)
            self.result_table.setRowCount(len(rows))

            for row_index, row_data in enumerate(rows):
                for col_index, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    self.result_table.setItem(row_index, col_index, item)

            # Display the record count
            self.record_count_label.setText(f"Record Count: {len(rows)}")

            # Close the database connection
            cursor.close()
            connection.close()
        except (Exception, psycopg2.Error) as error:
            print("Error executing query:", error)
            QMessageBox.critical(self, "Error", f"Error executing query:\n{error}")

    def export_to_excel(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")

            if file_path:
                data = []
                column_names = []
                for col in range(self.result_table.columnCount()):
                    column_names.append(self.result_table.horizontalHeaderItem(col).text())
                data.append(column_names)

                for row in range(self.result_table.rowCount()):
                    row_data = []
                    for col in range(self.result_table.columnCount()):
                        item = self.result_table.item(row, col)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append("")
                    data.append(row_data)

                df = pd.DataFrame(data[1:], columns=data[0])
                df.to_excel(file_path, index=False)

                QMessageBox.information(self, "Export Successful", f"Data exported to {file_path}")
        except Exception as error:
            QMessageBox.critical(self, "Export Error", f"Error exporting data:\n{error}")


if __name__ == "__main__":

    db_name = "database_name"
    db_user = "user_name"
    db_password = "password4"
    db_host = "host"
    db_port = "5432" #default

    app = QApplication(sys.argv)

    # Create a LoginWindow instance
    login_window = LoginWindow(db_name, db_user, db_password, db_host, db_port)

    # Open the LoginWindow and check the result
    if login_window.exec_() == QDialog.Accepted:
        # Retrieve the username and password from the LoginWindow
        username = login_window.username
        password = login_window.password

        # Create the LocationTab window with the username and password
        location_tab = LocationTab(db_name, db_user, password, db_host, db_port, username)

        # Create the DatabaseViewer window
        window = DatabaseViewer()
        window.setWindowTitle("Database Viewer")

        # Show the DatabaseViewer window
        window.show()

        # Start the event loop
        sys.exit(app.exec_())



