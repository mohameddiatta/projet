-- Script PostgreSQL 
-- Script pour créer les tables dans le schéma U_OPE de PostgreSQL pour ucab_senegal

CREATE SCHEMA IF NOT EXISTS U_OPE;

SET search_path TO U_OPE;

-- Table CustomUser
CREATE TABLE U_OPE.CustomUser (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    user_type VARCHAR(10) DEFAULT '1',
    password VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table AdminHOD
CREATE TABLE U_OPE.AdminHOD (
    id SERIAL PRIMARY KEY,
    admin_id INT REFERENCES U_OPE.CustomUser(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table Staffs
CREATE TABLE U_OPE.Staffs (
    id SERIAL PRIMARY KEY,
    admin_id INT REFERENCES U_OPE.CustomUser(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table Courses
CREATE TABLE U_OPE.Courses (
    id SERIAL PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table Subjects
CREATE TABLE U_OPE.Subjects (
    id SERIAL PRIMARY KEY,
    subject_name VARCHAR(255) NOT NULL,
    course_id INT REFERENCES U_OPE.Courses(id) ON DELETE CASCADE,
    staff_id INT REFERENCES U_OPE.Staffs(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table Students
CREATE TABLE U_OPE.Students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    gender VARCHAR(255) NOT NULL,
    profile_pic VARCHAR(255),
    address TEXT NOT NULL,
    course_id INT REFERENCES U_OPE.Courses(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table Attendance
CREATE TABLE U_OPE.Attendance (
    id SERIAL PRIMARY KEY,
    subject_id INT REFERENCES U_OPE.Subjects(id) ON DELETE CASCADE,
    attendance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table AttendanceReport
CREATE TABLE U_OPE.AttendanceReport (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES U_OPE.Students(id) ON DELETE CASCADE,
    attendance_id INT REFERENCES U_OPE.Attendance(id) ON DELETE CASCADE,
    status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table Niveau
CREATE TABLE U_OPE.Niveau (
    ID_Niveau SERIAL PRIMARY KEY,
    Nom_Niveau VARCHAR(255) NOT NULL
);

-- Table Filiere
CREATE TABLE U_OPE.Filiere (
    ID_Filiere SERIAL PRIMARY KEY,
    Nom_Filiere VARCHAR(255) NOT NULL,
    Quota_Max INT NOT NULL
);

-- Table Paiement
CREATE TABLE U_OPE.Paiement (
    ID_Paiement SERIAL PRIMARY KEY,
    Montant DECIMAL(10, 2) NOT NULL,
    Date_Paiement DATE NOT NULL,
    Methode VARCHAR(255) NOT NULL,
    Statut VARCHAR(255) NOT NULL,
    ID_Inscription INT REFERENCES U_OPE.Students(id) ON DELETE CASCADE
);

-- Table Notification
CREATE TABLE U_OPE.Notification (
    ID_Notification SERIAL PRIMARY KEY,
    Message TEXT NOT NULL,
    Date_Envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ID_Utilisateur INT REFERENCES U_OPE.CustomUser(id) ON DELETE CASCADE
);

-- Table Document
CREATE TABLE U_OPE.Document (
    ID_Document SERIAL PRIMARY KEY,
    Nom_Document VARCHAR(255) NOT NULL,
    Chemin_Fichier VARCHAR(255) NOT NULL,
    ID_Inscription INT REFERENCES U_OPE.Students(id) ON DELETE CASCADE
);
