INSERT INTO group_mc (id, mc_name)
VALUES
(1, 'Chang Yi'),
(2, 'Fong'),
(3, 'SSM'),
(4, 'Graf'),
(5, 'Ugolini'),
(6, 'Tecnorama'),
(7, 'Fadis'),
(8, 'DETTIN');

INSERT INTO machine (name, group_mc_id)
VALUES
('Chang Yi-1', 1),
('Chang Yi-2', 1),
('Chang Yi-3', 1),
('Chang Yi-4', 1),
('Chang Yi-5', 1),
('Fong-1', 2),
('Fong-2', 2),
('Fong-3', 2),
('Fong-4', 2),
('SSM-1', 3),
('SSM-2', 3),
('SSM-3', 3),
('SSM-4', 3),
('Graf-1', 4),
('Graf-2', 4),
('Graf-3', 4),
('Graf-4', 4),
('Ugolini-1', 5),
('Ugolini-2', 5),
('Ugolini-3', 5),
('Tecnorama-1', 6),
('Tecnorama-2', 6),
('Fadis-1', 7),
('Fadis-2', 7),
('DETTIN-1', 8);


INSERT INTO spare_parts (
    material_no, part_no, description, machine_type_id, bin, cost_center, price, stock, safety_stock, safety_stock_check
) VALUES
('SP001', 'P001', 'M0F67-MECHANICALSEAL', 1, 'A1', 'D.10', 50.00, 10, 20, TRUE),
('SP002', 'P002', 'MF86E-SL2HOSESCREWONCONNECTIONWITHMALETHREAD618', 2, 'A2', 'CC002', 75.00, 150, 30, FALSE),
('SP003', 'P003', 'MC1E9-SL2CERAMICSPLITEYELETD68H6D28MM', 1, 'B1', 'D.11', 20.00, 60, 15, TRUE),
('SP004', 'P004', 'MC29E-SL2AGCERAMICSPLITEYELETD65H68D38MM', 1, 'B2', 'CC003', 25.00, 80, 20, TRUE),
('SP005', 'P005', 'MD7A5-SL2PUGLASSCOVERGEARS', 2, 'B3', 'CC004', 18.00, 40, 10, FALSE),
('SP006', 'P006', 'M1E71-SL2SEALRUBBER', 2, 'B4', 'D.12', 12.50, 90, 25, FALSE),
('SP007', 'P007', 'MB509-BEARING60002Z', 1, 'C1', 'D.13', 10.00, 100, 30, TRUE),
('SP008', 'P008', 'MB862-HOSEPVCTRANSPARENT64X1MM', 3, 'C2', 'D.14', 15.00, 70, 20, TRUE),
('SP009', 'P009', 'MAB39-NEEDLEFORPWINDING69MMLI', 3, 'C3', 'CC005', 7.50, 30, 10, FALSE),
('SP010', 'P010', 'MC40B-SUPPLYPACKAGEPLATE', 1, 'C4', 'D.15', 22.00, 45, 15, TRUE),
('SP011', 'P011', 'M5BF7-NAN', 2, 'D1', 'CC006', 30.00, 50, 20, FALSE);



INSERT INTO machine_pos (mc_pos, mc_id)
VALUES 
('POS1', 1),
('POS2', 1),
('POS3', 1),
('POS5', 1),
('FO1', 2),
('FO2', 2),
('FO3', 2),
('SM1', 3),
('SM2', 3),
('SM3', 3),
('GR1', 4),
('GR2', 4),
('GR3', 4),
('GR4', 4),
('GR5', 4),
('UGO1', 5),
('UGO2', 5),
('UGO3', 5),
('UGO4', 5);
ALTER TABLE spare_parts
ADD COLUMN image_url VARCHAR(255);

INSERT INTO import_export (part_id, quantity, mc_pos_id, empl_id, date, reason, im_ex_flag) 
VALUES 
    ('SP001', 100, 'POS1', 'EMP001', '2025-05-10', 'Nhập hàng để thay thế', TRUE),
    ('SP002', 50, 'FO1', 'EMP002', '2025-05-11', 'Xuất hàng cho bảo trì', FALSE),
    ('SP003', 200, 'SM1', 'EMP003', '2025-05-12', 'Nhập hàng để bổ sung kho', TRUE),
    ('SP004', 10, 'GR1', 'EMP004', '2025-05-13', 'Xuất hàng cho sửa chữa', FALSE),
    ('SP005', 150, 'UGO1', 'EMP005', '2025-05-14', 'Nhập hàng từ nhà cung cấp', TRUE);


UPDATE employees SET 
    birthday = '1991-01-10',
    start_date = '2019-03-15',
    check_in_time = '08:00:00',
    check_out_time = '17:00:00',
    address = 'Tam Kỳ',
    phone_number = '0901234501',
    email = 'nguyenvana@amann.com',
    gender = 'Nam'
WHERE amann_id = 'EMP001';

UPDATE employees SET 
    birthday = '1992-02-12',
    start_date = '2020-04-18',
    check_in_time = '08:00:00',
    check_out_time = '17:00:00',
    address = 'Đà Nẵng',
    phone_number = '0901234502',
    email = 'tranthib@amann.com',
    gender = 'Nữ'
WHERE amann_id = 'EMP002';

UPDATE employees SET 
    birthday = '1993-03-20',
    start_date = '2021-05-10',
    check_in_time = '08:30:00',
    check_out_time = '17:30:00',
    address = 'Tam Kỳ',
    phone_number = '0901234503',
    email = 'hoangtrung@amann.com',
    gender = 'Nam'
WHERE amann_id = 'EMP003';

UPDATE employees SET 
    birthday = '1995-06-25',
    start_date = '2018-06-01',
    check_in_time = '08:00:00',
    check_out_time = '16:30:00',
    address = 'TP.HCM',
    phone_number = '0901234504',
    email = 'lehoang@amann.com',
    gender = 'Nam'
WHERE amann_id = 'EMP004';

UPDATE employees SET 
    birthday = '1990-07-15',
    start_date = '2020-01-15',
    check_in_time = '09:00:00',
    check_out_time = '18:00:00',
    address = 'Tam Kỳ',
    phone_number = '0901234505',
    email = 'ngoclan@amann.com',
    gender = 'Nữ'
WHERE amann_id = 'EMP005';

UPDATE employees SET 
    birthday = '1994-10-05',
    start_date = '2021-07-20',
    check_in_time = '08:00:00',
    check_out_time = '17:00:00',
    address = 'Số 16, Quận 6, TP.HCM',
    phone_number = '0901234506',
    email = 'thanhnguyen@amann.com',
    gender = 'Nam'
WHERE amann_id = 'EMP006';

UPDATE employees SET 
    birthday = '1996-11-23',
    start_date = '2022-08-30',
    check_in_time = '08:30:00',
    check_out_time = '17:30:00',
    address = 'Tam Kỳ',
    phone_number = '0901234507',
    email = 'khanhhoa@amann.com',
    gender = 'Nữ'
WHERE amann_id = 'EMP007';

UPDATE employees SET 
    birthday = '1990-12-01',
    start_date = '2019-09-10',
    check_in_time = '08:00:00',
    check_out_time = '16:30:00',
    address = 'Đà Nẵng',
    phone_number = '0901234508',
    email = 'ducphat@amann.com',
    gender = 'Nam'
WHERE amann_id = 'EMP008';

UPDATE employees SET 
    birthday = '1995-09-18',
    start_date = '2021-04-01',
    check_in_time = '09:00:00',
    check_out_time = '18:00:00',
    address = 'Đà Nẵng',
    phone_number = '0901234509',
    email = 'tungtien@amann.com',
    gender = 'Nam'
WHERE amann_id = 'EMP009';

UPDATE employees SET 
    birthday = '1990-05-10',
    start_date = '2020-02-20',
    check_in_time = '08:30:00',
    check_out_time = '17:30:00',
    address = 'Huế',
    phone_number = '0901234510',
    email = 'thuylinh@amann.com',
    gender = 'Nữ'
WHERE amann_id = 'EMP010';

UPDATE employees SET 
    birthday = '1992-04-22',
    start_date = '2021-09-05',
    check_in_time = '08:00:00',
    check_out_time = '16:30:00',
    address = 'Huế',
    phone_number = '0901234511',
    email = 'baohien@amann.com',
    gender = 'Nữ'
WHERE amann_id = 'EMP011';

UPDATE employees SET 
    birthday = '1989-03-03',
    start_date = '2021-05-05',
    check_in_time = '09:00:00',
    check_out_time = '18:00:00',
    address = 'Tam Kỳ',
    phone_number = '0901234512',
    email = 'quanghieu@amann.com',
    gender = 'Nam'
WHERE amann_id = '23';




UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP001';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP002';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP003';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP004';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP005';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP006';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP007';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP008';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP009';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP010';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = 'EMP011';

UPDATE employees SET 
    age = YEAR(CURDATE()) - YEAR(birthday),
    years_worked = YEAR(CURDATE()) - YEAR(start_date)
WHERE amann_id = '23';
