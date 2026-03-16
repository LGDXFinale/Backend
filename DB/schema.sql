CREATE DATABASE IF NOT EXISTS dx_wash_service
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_general_ci;

USE dx_wash_service;

-- 1. 회원 정보
CREATE TABLE member_info (
    member_id       VARCHAR(50)  NOT NULL,
    name            VARCHAR(50)  NOT NULL,
    phone_number    VARCHAR(20)  NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (member_id)
);

-- 2. 세탁 프로그램
CREATE TABLE wash_program (
    program_id      VARCHAR(50)  NOT NULL,
    program_name    VARCHAR(50)  NOT NULL,
    PRIMARY KEY (program_id)
);

-- 3. 세탁기 정보
CREATE TABLE washer_info (
    washer_id       VARCHAR(50)  NOT NULL,
    member_id       VARCHAR(50)  NOT NULL,
    model_name      VARCHAR(100) NOT NULL,
    install_at      DATETIME     NOT NULL,
    PRIMARY KEY (washer_id),
    CONSTRAINT fk_washer_member
        FOREIGN KEY (member_id) REFERENCES member_info(member_id)
);

-- 4. 현재 적재량 정보
CREATE TABLE load_info (
    load_id             VARCHAR(50)   NOT NULL,
    current_weight      DECIMAL(10,2) NOT NULL,
    member_id           VARCHAR(50)   NOT NULL,
    load_ratio          DECIMAL(5,2)  NOT NULL,
    measured_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (load_id),
    CONSTRAINT fk_load_member
        FOREIGN KEY (member_id) REFERENCES member_info(member_id)
);

-- 5. 세탁 추천
CREATE TABLE recommendation (
    recommendation_id   VARCHAR(50)  NOT NULL,
    member_id           VARCHAR(50)  NOT NULL,
    recommended_time    DATETIME     NOT NULL,
    accepted_yn         TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (recommendation_id),
    CONSTRAINT fk_recommendation_member
        FOREIGN KEY (member_id) REFERENCES member_info(member_id)
);

-- 6. 세탁 이력
CREATE TABLE wash_history (
    wash_id             VARCHAR(50)   NOT NULL,
    member_id           VARCHAR(50)   NOT NULL,
    washer_id           VARCHAR(50)   NOT NULL,
    program_id          VARCHAR(50)   NOT NULL,
    start_time          DATETIME      NOT NULL,
    end_time            DATETIME      NOT NULL,
    total_weight        DECIMAL(10,2) NOT NULL,
    humidity            DECIMAL(5,2)  NOT NULL,
    temperature         DECIMAL(5,2)  NOT NULL,
    PRIMARY KEY (wash_id),
    CONSTRAINT fk_history_member
        FOREIGN KEY (member_id) REFERENCES member_info(member_id),
    CONSTRAINT fk_history_washer
        FOREIGN KEY (washer_id) REFERENCES washer_info(washer_id),
    CONSTRAINT fk_history_program
        FOREIGN KEY (program_id) REFERENCES wash_program(program_id)
);

-- 7. 세탁 진행 상태
CREATE TABLE wash_status (
    wash_status_id        VARCHAR(50)   NOT NULL,
    wash_id               VARCHAR(50)   NOT NULL,
    washer_id             VARCHAR(50)   NOT NULL,

    conta_level           DECIMAL(5,2)  NOT NULL,   -- 시작 오염도
    current_conta_level   DECIMAL(5,2)  NOT NULL,   -- 현재 남은 오염도
    cleaned_ratio         DECIMAL(5,2)  NOT NULL,   -- 세척 완료율(%)

    current_stage         VARCHAR(50)   NOT NULL,   -- 세탁중/헹굼중/탈수중/종료
    progress_percent      DECIMAL(5,2)  NOT NULL,   -- 전체 진행률(%)

    remaining_time        INT           NULL,       -- 남은 시간(분)
    expected_end_time     DATETIME      NULL,       -- 예상 종료 시각
    updated_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (wash_status_id),

    CONSTRAINT fk_status_wash
        FOREIGN KEY (wash_id) REFERENCES wash_history(wash_id),

    CONSTRAINT fk_status_washer
        FOREIGN KEY (washer_id) REFERENCES washer_info(washer_id)
);

-- 8. 센서 데이터
CREATE TABLE sensor_data (
    sensor_id           VARCHAR(50)   NOT NULL,
    washer_id           VARCHAR(50)   NOT NULL,
    sensor_model_id     VARCHAR(50)   NOT NULL,
    measured_value      DECIMAL(10,2) NOT NULL,
    unit                VARCHAR(20)   NOT NULL,
    measured_at         DATETIME      NOT NULL,
    PRIMARY KEY (sensor_id),
    CONSTRAINT fk_sensor_washer
        FOREIGN KEY (washer_id) REFERENCES washer_info(washer_id)
);

-- 9. 세탁물 정보
CREATE TABLE wash_cloth_info (
    cloth_id            VARCHAR(50)   NOT NULL,
    washer_id           VARCHAR(50)   NOT NULL,
    cloth_weight        DECIMAL(10,2) NOT NULL,
    cloth_type          VARCHAR(50)   NOT NULL,
    cloth_color         VARCHAR(50)   NOT NULL,
    load_status         VARCHAR(50)   NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cloth_id),
    CONSTRAINT fk_cloth_washer
        FOREIGN KEY (washer_id) REFERENCES washer_info(washer_id)
);

-- 10. 건조 추천
CREATE TABLE dry_recommendation (
    dry_rec_id          VARCHAR(50)  NOT NULL,
    dry_rec_time        DATETIME     NOT NULL,
    dry_rec_method      VARCHAR(50)  NOT NULL,
    PRIMARY KEY (dry_rec_id)
);